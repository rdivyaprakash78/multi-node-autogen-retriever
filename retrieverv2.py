# imports

import autogen
from promtpsv2 import prompts
from pydantic import BaseModel, Field
from typing import Literal, Dict, Annotated, List
from langchain.output_parsers import PydanticOutputParser
from langchain_community.utilities import WikipediaAPIWrapper

# llm configuration

llm_config = {
    "cache_seed": None,
    "config_list": [
        {
        "model": "llama-3.1-8b-instant", 
        "api_key": "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", 
        "api_type": "groq"
        }
    ],

}

def get_response(user_input):

    # Initial group chat agents

    query_splitter = autogen.AssistantAgent(
        name = "query splitter",
        system_message = prompts["query splitter"],
        llm_config= llm_config
    )

    class subquery(BaseModel):
        subquery: str = Field(description= "Subquery")
        category: Literal["wiki", "time", "general"] = Field(description= "Category of the subquery")

    class queries(BaseModel):
        queries : List[subquery] = Field(description="List of subquery object. Each object contains the subquery and the corresponding category")

    parser = PydanticOutputParser(pydantic_object= queries)

    classifier = autogen.AssistantAgent(
        name = "Classifier",
        system_message = prompts["classifier"]+ "\n\n" + str(parser.get_format_instructions()),
        llm_config= llm_config
    )

    admin = autogen.UserProxyAgent(
        name = "Admin",
        system_message = "You are an human admin. You will execute fuctions whenever needed. You can also execute codes if necessary.",
        code_execution_config={
            "work_dir": "code",
            "use_docker": False
        },
        human_input_mode="NEVER",
        llm_config=llm_config
    )

    # Intial group chat configuration

    def custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
        messages = groupchat.messages

        if len(messages) <=1:
            return query_splitter
        elif last_speaker is query_splitter:
            return classifier
        
        return None


    groupchat1 = autogen.GroupChat(
        agents=[admin, query_splitter, classifier],
        messages=[],
        speaker_selection_method=custom_speaker_selection_func
    )

    manager1 = autogen.GroupChatManager(groupchat=groupchat1, llm_config=llm_config)

    message = prompts["system message"].format(query = user_input)
    try :
        chat_result1 = admin.initiate_chat(manager1, message=message)
    except Exception as e:
        return "Failed to initiate function call. Try again."
    
    query_and_category_before_parsing = chat_result1.chat_history[-1]["content"]
    try:
        query_and_category = parser.parse(query_and_category_before_parsing.lower())
    except Exception as e:
        return "Parsing error please try again"
    
    result = query_and_category.queries

    flows = {
        "wiki" : ["wiki", "admin", "retriever"],
        "time" : ["code_generater", "admin", "retriever"],
        "general" : ["assistant", "retriever"],
        }
    
    path = []

    print(result)

    path = [item.category for item in result]

    flow = []
    for agent in path:
        flow.append(flows[agent])

    print("path : ", flow)
    flow = [item for sublist in flow for item in sublist]
    print("path : ", flow)


    # Final group chat agents

    planner = autogen.AssistantAgent(
        name = "Planner",
        system_message= prompts["planner"],
        llm_config= llm_config
    )

    assistant = autogen.AssistantAgent(
        name = "Assistant",
        system_message= prompts["assistant"],
        llm_config= llm_config
    )

    wiki = autogen.AssistantAgent(
        name = "Wiki",
        system_message= prompts["wiki"],
        llm_config= llm_config
    )

    code_generater = autogen.AssistantAgent(
        name = "Code Generater",
        system_message= prompts["code generater"],
        llm_config= llm_config
    )

    retriever = autogen.AssistantAgent(
        name = "Retriever",
        system_message= prompts["retriever"],
        llm_config= llm_config
    )

    final_retriever = autogen.AssistantAgent(
        name = "Final Retriever",
        system_message= prompts["final answer retriever"],
        llm_config= llm_config
    )

    def wiki_fetcher(search_term: Annotated[str, "wikipedia search term"], user_query: Annotated[str, "query that needs to be answered"])-> Annotated[str, "wikipedia search result"]:
        wiki = WikipediaAPIWrapper()
        search_results = str(wiki.run(search_term))
        prompt = f"Here's the result : \n\n {search_results}, \n\n answer the user query : {user_query}"
        return prompt

    wiki.register_for_llm(name="wiki_fetcher", description="Wiki search engine")(wiki_fetcher)
    admin.register_for_execution(name="wiki_fetcher")(wiki_fetcher)

    path_def = {
        "wiki" : wiki,
        "admin" : admin,
        "retriever" : retriever,
        "code_generater" : code_generater,
        "assistant" : assistant
    }
    
    final_path = []
    for i in flow:
        final_path.append(path_def[i])

    final_path.append(final_retriever)

    # Final group chat configurations
    counter = 0
    def final_custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
        nonlocal counter, final_path
        messages = groupchat.messages

        if len(messages) <=1:
            return planner
        elif counter < len(final_path):
            counter += 1
            return final_path[counter-1]
        return None
        

    groupchat2 = autogen.GroupChat(
        agents=[planner, assistant, code_generater, retriever, admin, wiki, final_retriever],
        messages=[],
        speaker_selection_method=final_custom_speaker_selection_func,
        max_round= 30
    )

    manager2 = autogen.GroupChatManager(groupchat=groupchat2, llm_config=llm_config)
    try :
        chat_result2 = admin.initiate_chat(manager2, message=prompts["final system message"].format(query_dict=result, flow=path))
    except Exception as e:
        return "Failed to initiate function call. Try again."
    final_chat_history = list(chat_result1.chat_history) + list(chat_result2.chat_history)

    return final_chat_history
