import autogen
from promtpsv2 import prompts
from pydantic import BaseModel, Field
from typing import Literal, Dict, Annotated
from langchain.output_parsers import PydanticOutputParser
from langchain_community.utilities import WikipediaAPIWrapper

llm_config = {
    "cache_seed": None,
    "config_list": [
        {
        "model": "llama-3.3-70b-versatile", 
        "api_key": "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", 
        "api_type": "groq"
        }
    ]
}


query_splitter = autogen.AssistantAgent(
    name = "query splitter",
    system_message = prompts["query splitter"],
    llm_config= llm_config
)

class queries(BaseModel):
    query_category_pair: Dict[str, str] = Field(
        default={},
        description="A dictionary that maps query strings (keys) to category strings (values)."
    )

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

def custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
    messages = groupchat.messages

    if len(messages) <=1:
        return query_splitter
    elif last_speaker is query_splitter:
        return classifier
    
    return None


groupchat = autogen.GroupChat(
    agents=[admin, query_splitter, classifier],
    messages=[],
    speaker_selection_method=custom_speaker_selection_func
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

user_input = input("user input :")

message = prompts["system message"].format(query = user_input)
chat_result = admin.initiate_chat(manager, message=message)

query_and_category_before_parsing = chat_result.chat_history[-1]["content"]
query_and_category = parser.parse(query_and_category_before_parsing.lower())

#print("parsed output : ", query_and_category)
result = query_and_category.query_category_pair

flows = {
    "wiki" : ["planner", "assistant", "admin", "retriever"],
    "time" : ["planner", "code_generater", "admin", "retriever"],
    "general" : ["planner", "assistant", "admin", "retriever"]
}

path = []

for category in result.values():
    path.append(flows[category])

path = [agent for flow in path for agent in flow]

print("path : ", path)

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

def wiki_fetcher(search_term: Annotated[str, "wikipedia search term"], user_query: Annotated[str, "query that needs to be answered"])-> Annotated[str, "wikipedia search result"]:
    wiki = WikipediaAPIWrapper()
    search_results = str(wiki.run(search_term))
    prompt = f"Here's the result : \n\n {search_results}, \n\n answer the user query : {user_query}"
    return prompt

assistant.register_for_llm(name="wiki_fetcher", description="Wiki search engine")(wiki_fetcher)
admin.register_for_execution(name="wiki_fetcher")(wiki_fetcher)

counter = 0
def final_custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
    global counter, path
    messages = groupchat.messages

    if len(messages) <=1:
        counter += 1
        return globals()[path[counter-1]]
    elif counter < len(path):
        counter += 1
        return globals()[path[counter-1]]
    
    return None

groupchat = autogen.GroupChat(
    agents=[planner, assistant, code_generater, retriever, admin],
    messages=[],
    speaker_selection_method=final_custom_speaker_selection_func
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
chat_result = admin.initiate_chat(manager, message=prompts["final system message"].format(query_dict=result, flow=path))

print("Final chat result : ", chat_result.chat_history[-1]["content"])

