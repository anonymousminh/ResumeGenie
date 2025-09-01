import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Initialize a free embedding model from Hugging Face
# This model is free and doesn't require API keys
embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_text_embedding(text: str) -> list[float]:
    """
    Generates an embedding for the given text using a free embedding model.

    Args:
        text (str): The text to generate an embedding for

    Returns:
        list[float]: A list of floating-point numbers representing the text embedding
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    try:
        # Generate embedding using the free model
        embedding = embeddings_model.encode(text)
        # Convert numpy array to list of floats
        return embedding.tolist()
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {str(e)}")


def get_multiple_text_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings for multiple texts using a free embedding model.

    Args:
        texts (list[str]): A list of texts to generate embeddings for

    Returns:
        list[list[float]]: A list of embeddings, each as a list of floating-point numbers
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")

    try:
        # Generate embeddings for multiple texts
        embeddings = embeddings_model.encode(texts)
        # Convert numpy arrays to list of lists of floats
        return [embedding.tolist() for embedding in embeddings]
    except Exception as e:
        raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
