# backend/embedding_utils.py

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI embedding model
# This will use the text-embedding-ada-002 model by default
# Ensure OPENAI_API_KEY is set in your environment variables or .env file
embeddings_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))


def get_text_embedding(text: str) -> list[float]:
    """
    Generates an embedding for the given text using OpenAI's embedding model.

    Args:
        text (str): The text to generate an embedding for

    Returns:
        list[float]: A list of floating-point numbers representing the text embedding
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    try:
        embedding = embeddings_model.embed_query(text)
        return embedding
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {str(e)}")


def get_multiple_text_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for multiple texts using OpenAI's embedding model.

    Args:
        texts (list[str]): A list of texts to generate embeddings for

    Returns:
        list[list[float]]: A list of embeddings, each as a list of floating-point numbers
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")

    try:
        embeddings = embeddings_model.embed_documents(texts)
        return embeddings
    except Exception as e:
        raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
