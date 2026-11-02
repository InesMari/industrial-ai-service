import os
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model="qwen-plus",  # 或 qwen-max，以百炼控制台为准
    model_provider="openai",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)