import autogen
import json
from pydantic import BaseModel, ValidationError
from promtpsv2 import prompts

class UserData(BaseModel):
    name: str
    age: int
    job_role: str

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
    name="flow planner",
    system_message= prompts["flow planner"],
    llm_config=llm_config
)

query_splitter = autogen.ConversableAgent(
    name="query splitter",
    system_message= prompts["query splitter"],
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
    llm_config=llm_config
)

groupchat = autogen.GroupChat(
    agents=[flow_planner, query_splitter, admin],
    messages=[],
    max_round=3
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
request = str(input("user request : "))
message = prompts["system_message"].format(query = request)
chat_result = admin.initiate_chat(
    manager,
    message=message)