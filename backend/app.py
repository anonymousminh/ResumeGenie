# backend/app.py

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()

# Get Claude API key from environment variable
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

# Initialize Claude LLM
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.7,
    anthropic_api_key=ANTHROPIC_API_KEY,
)

# Create a simple prompt template
prompt = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful AI assistant."), ("user", "{input}")]
)

# Create a simple chain
chain = prompt | llm

if __name__ == "__main__":
    print("Testing LangChain with Claude...")
    response = chain.invoke({"input": "What is the capital of France?"})
    print(response.content)
