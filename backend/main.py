from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from parser_utils import parse_document
from embedding_utils import get_text_embedding  # Import the embedding utility
import pymysql
import json
import uuid  # For generating unique IDs
import numpy as np
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# AWS S3 Configuration
S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")
S3_REGION = os.getenv("AWS_REGION")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=S3_REGION,
)

# TiDB Connection Details
DB_HOST = os.getenv("TIDB_HOST")
DB_PORT = int(os.getenv("TIDB_PORT", 4000))
DB_USER = os.getenv("TIDB_USER")
DB_PASSWORD = os.getenv("TIDB_PASSWORD")
DB_NAME = os.getenv("TIDB_NAME", "test")  # Default database name


def connect_to_tidb():
    """Establishes a connection to TiDB Serverless."""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True,
            ssl={
                "ssl": {"ssl_mode": "VERIFY_IDENTITY"}
            },  # Ensure changes are committed
        )
        return conn
    except Exception as e:
        print(f"Error connecting to TiDB: {e}")
        return None


# Initialize the Claude LLM
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.7,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)


@app.route("/")
def home():
    return jsonify(
        {
            "message": "AI Career Coach API is running!",
            "endpoints": {
                "upload_resume": "/upload_resume (POST)",
                "process_documents": "/process_documents (POST)",
                "vector_search": "/vector_search (POST)",
                "generate_text": "/generate_text (POST)",
            },
        }
    )


@app.route("/upload_resume", methods=["POST"])
def upload_resume_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    resume_file_b64 = data.get("resumeFileBase64")
    resume_file_name = data.get("resumeFileName")
    resume_file_type = data.get("resumeFileType")
    job_posting_text = data.get("jobPostingText")

    if (
        not resume_file_b64
        or not resume_file_name
        or not resume_file_type
        or not job_posting_text
    ):
        return (
            jsonify({"error": "Missing resume file, name, type, or job posting text"}),
            400,
        )

    try:
        resume_bytes = base64.b64decode(resume_file_b64)
        s3_key = f"resumes/{resume_file_name}"

        s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=resume_bytes)

        s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        return jsonify(
            {
                "message": "File uploaded to S3 successfully!",
                "s3Url": s3_url,
                "jobPostingText": job_posting_text,
                "resumeFileType": resume_file_type,
            }
        )
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/process_documents", methods=["POST"])
def process_documents_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    s3_url = data.get("s3Url")
    resume_file_type = data.get("resumeFileType")
    job_posting_text = data.get("jobPostingText")

    if not s3_url or not resume_file_type or not job_posting_text:
        return (
            jsonify({"error": "Missing S3 URL, resume file type, or job posting text"}),
            400,
        )

    conn = None
    try:
        # Extract bucket name and key from S3 URL
        path_parts = s3_url.split("/")
        bucket_name_from_url = path_parts[2].split(".")[0]
        s3_key = "/".join(path_parts[3:])

        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name_from_url, Key=s3_key)
        resume_bytes = response["Body"].read()

        # Parse the document
        parsed_resume_text = parse_document(resume_bytes, resume_file_type)

        # Generate embeddings
        resume_embedding = get_text_embedding(parsed_resume_text)
        job_posting_embedding = get_text_embedding(job_posting_text)

        # Save to TiDB
        conn = connect_to_tidb()
        if conn:
            cursor = conn.cursor()
            # Save resume
            resume_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO resumes (id, file_name, s3_url, raw_text, embedding) VALUES (%s, %s, %s, %s, %s)",
                (
                    resume_id,
                    os.path.basename(s3_key),
                    s3_url,
                    parsed_resume_text,
                    json.dumps(resume_embedding),
                ),
            )
            # Save job posting
            job_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO job_postings (id, raw_text, embedding) VALUES (%s, %s, %s)",
                (job_id, job_posting_text, json.dumps(job_posting_embedding)),
            )
            conn.commit()
            cursor.close()
        else:
            return jsonify({"error": "Could not connect to database"}), 500

        return jsonify(
            {
                "parsedResumeText": parsed_resume_text,
                "parsedJobPostingText": job_posting_text,
                "resumeEmbedding": resume_embedding,
                "jobPostingEmbedding": job_posting_embedding,
            }
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return jsonify({"error": "File not found in S3"}), 404
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


def cosine_similarity(vec1, vec2):
    """Calculates the cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


@app.route("/vector_search", methods=["POST"])
def vector_search_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    query_embedding = data.get("queryEmbedding")
    search_type = data.get("searchType")  # e.g., "resumes" or "courses"
    limit = data.get("limit", 5)  # Number of results to return

    if not query_embedding or not search_type:
        return jsonify({"error": "Missing query embedding or search type"}), 400

    conn = None
    try:
        conn = connect_to_tidb()
        if not conn:
            return jsonify({"error": "Could not connect to database"}), 500

        cursor = conn.cursor()
        results = []

        if search_type == "resumes":
            cursor.execute("SELECT id, file_name, raw_text, embedding FROM resumes;")
            for resume_id, file_name, raw_text, embedding_json in cursor.fetchall():
                resume_embedding = json.loads(embedding_json)
                similarity = cosine_similarity(query_embedding, resume_embedding)
                results.append(
                    {
                        "id": resume_id,
                        "file_name": file_name,
                        "raw_text_preview": raw_text[:200] + "...",
                        "similarity": similarity,
                    }
                )
            # Sort by similarity in descending order
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return jsonify({"results": results[:limit]})

        elif search_type == "courses":
            cursor.execute("SELECT id, name, description, url, embedding FROM courses;")
            for course_id, name, description, url, embedding_json in cursor.fetchall():
                course_embedding = json.loads(embedding_json)
                similarity = cosine_similarity(query_embedding, course_embedding)
                results.append(
                    {
                        "id": course_id,
                        "name": name,
                        "description_preview": description[:200] + "...",
                        "url": url,
                        "similarity": similarity,
                    }
                )
            # Sort by similarity in descending order
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return jsonify({"results": results[:limit]})

        else:
            return jsonify({"error": "Invalid search type"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


# Example of a simple chain using Claude (can be integrated into an endpoint later)
@app.route("/generate_text", methods=["POST"])
def generate_text_endpoint():
    data = request.json
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    user_prompt = data["prompt"]

    try:
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", "You are a helpful AI assistant."), ("user", "{input}")]
        )
        chain = prompt_template | llm
        response = chain.invoke({"input": user_prompt})
        return jsonify({"generated_text": response.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/rewrite_bullet", methods=["POST"])
def rewrite_bullet_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    bullet_point = data.get("bulletPoint")
    job_description = data.get("jobDescription")

    if not bullet_point or not job_description:
        return jsonify({"error": "Missing bullet point or job description"}), 400

    try:
        # Define the prompt template for bullet point rewriting
        rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert resume writer. Your task is to rewrite a given resume bullet point to be more impactful, quantifiable, and tailored to a specific job description. Focus on achievements and results, using strong action verbs. Ensure the rewritten bullet point is concise and relevant to the job requirements.",
                ),
                (
                    "user",
                    "Original Resume Bullet Point: {bullet_point}\n\nJob Description:\n{job_description}\n\nRewrite the resume bullet point to be more impactful and relevant to the job description. Start directly with the rewritten bullet point, no introductory phrases.",
                ),
            ]
        )

        # Create the chain: Prompt -> LLM -> Output Parser
        rewrite_chain = rewrite_prompt | llm | StrOutputParser()

        # Invoke the chain with the provided inputs
        rewritten_bullet = rewrite_chain.invoke(
            {"bullet_point": bullet_point, "job_description": job_description}
        )

        return jsonify({"rewrittenBullet": rewritten_bullet})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
