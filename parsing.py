import autogen
import json
from pydantic import BaseModel, ValidationError
from promtpsv2 import prompts
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

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

class query(BaseModel):
    queries : list = Field(description= "String List of queries")

parser = PydanticOutputParser(pydantic_object=query)

flow_planner = autogen.ConversableAgent(
    name="flow planner",
    system_message= prompts["flow planner"],
    llm_config=llm_config
)

query_splitter = autogen.ConversableAgent(
    name="query splitter",
    system_message= prompts["query splitter"] + "\n\n" + str(parser.get_format_instructions()) , 
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

query = str(input("user query : "))


chat_result = admin.initiate_chat(query_splitter,
    message=prompts["system_message"].format(query=query),
    summary_method="reflection_with_llm",
    max_turns=1,
)

response = chat_result.chat_history[-1]["content"]
response_values = parser.parse(response)

print(response_values.queries)



