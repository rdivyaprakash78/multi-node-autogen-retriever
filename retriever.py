import autogen
from typing import Annotated
from langchain_community.utilities import WikipediaAPIWrapper
import regex as re
from prompts import prompts

llm_config = {
    "cache_seed": None,
    "config_list": [
        {
        "model": "llama-3.1-70b-versatile", 
        "api_key": "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", 
        "api_type": "groq"
        }
    ]
}

flow_planner = autogen.ConversableAgent(
    name="Flow Planner",
    system_message=prompts["flow planner prompt"],
    llm_config=llm_config
)

query_splitter = autogen.ConversableAgent(
    name = "Query Splitter",
    system_message=prompts["query splitter prompt"],
    llm_config=llm_config
)

planner = autogen.ConversableAgent(
    name="Planner",
    system_message=prompts["planner prompt"],
    llm_config=llm_config
)

assistant = autogen.AssistantAgent(
    name="Assistant",
    system_message=prompts["assistant prompt"],
    llm_config=llm_config
)

code_generater = autogen.AssistantAgent(
    name="Code generater",
    system_message=prompts["code generater prompt"],
    llm_config=llm_config
)

retriever = autogen.ConversableAgent(
    name="Answer retriever",
    system_message=prompts["retriever prompt"],
    llm_config=llm_config
)

admin = autogen.UserProxyAgent(
    name ="Admin",
    system_message= "You are an human admin.",
    code_execution_config={
        "work_dir": "code",
        "use_docker": False
    },
    human_input_mode="NEVER",
    llm_config=False
)

#wiki fetching tool
def wiki_fetcher(search_term: Annotated[str, "wikipedia search term"], user_query: Annotated[str, "query that needs to be answered"])-> Annotated[str, "wikipedia search result"]:
    wiki = WikipediaAPIWrapper()
    search_results = str(wiki.run(search_term))
    prompt = f"Here's the result : \n\n {search_results}, \n\n answer the user query : {user_query}"
    return prompt

assistant.register_for_llm(name="wiki_fetcher", description="Wiki search engine")(wiki_fetcher)
admin.register_for_execution(name="wiki_fetcher")(wiki_fetcher)

counter = 0
history = ""
flow = []
def custom_speaker_selection_func(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
    global counter
    global history
    global flow

    messages = groupchat.messages
    
    if len(messages) <= 1:
        return flow_planner
    elif len(messages) == 2:
        history = messages[-1]["content"]
        match = re.search(r'response\s*:\s*\[(.*?)\]', history.lower())
        flow = [item.strip().strip('"') for item in match.group(1).split(',')]
        counter += 1
        return globals()[flow[counter-1]]
    elif counter < len(flow):
        counter += 1

        return globals()[flow[counter-1]]
    else:
        return None
    

groupchat = autogen.GroupChat(
    agents=[flow_planner, query_splitter, planner, assistant, code_generater, retriever, admin],
    messages=[],
    # speaker_selection_method=custom_speaker_selection_func
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

user_request = "Compare between AMD EPYC processors and ryzen "
message = f"user_query : {user_request}. Remember the 'user_query' throughout the conversation."

chat_result = admin.initiate_chat(
    manager,
    message=message,
)

