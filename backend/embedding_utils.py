# backend/embedding_utils.py

from langchain_community.embeddings import HuggingFaceEmbeddings

# from langchain_openai import OpenAIEmbeddings # Uncomment if using OpenAI

# Initialize embedding model
# For local models, use HuggingFaceEmbeddings
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings_model = HuggingFaceEmbeddings(model_name=model_name)

# For OpenAI embeddings (requires OPENAI_API_KEY environment variable)
# embeddings_model = OpenAIEmbeddings()

# Placeholder for the chosen embedding model
# You will uncomment and configure one of the above based on your choice
# embeddings_model = None # Replace with actual initialization


def get_text_embedding(text: str) -> list[float]:
    """Generates an embedding for the given text."""
    if embeddings_model is None:
        raise ValueError(
            "Embedding model not initialized. Choose HuggingFaceEmbeddings or OpenAIEmbeddings."
        )
    return embeddings_model.embed_query(text)


# Example of how to initialize (choose one):
# embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# Or if you have OpenAI API key:
# import os
# os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
# embeddings_model = OpenAIEmbeddings()
