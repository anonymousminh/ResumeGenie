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
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import BaseOutputParser
from typing import Dict, Any
from pydantic import BaseModel, Field
import requests
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import io

# Load environment variables from .env file
load_dotenv()


def validate_environment_variables():
    """Validate that all required environment variables are set."""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "AWS_S3_BUCKET_NAME",
        "AWS_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "TIDB_HOST",
        "TIDB_USER",
        "TIDB_PASSWORD",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


# Validate environment variables on startup
try:
    validate_environment_variables()
except EnvironmentError as e:
    print(f"Environment Error: {e}")
    print(
        "Please create a .env file with the required variables. See .env.example for reference."
    )

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


def extract_skills_from_text(text_to_analyze: str):
    """Helper function to extract skills from text without making HTTP requests."""
    try:
        parser = JsonOutputParser(pydantic_object=Skills)

        skill_extraction_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at identifying and extracting technical and soft skills from text. "
                    "Extract a comprehensive list of distinct skills. You must respond with ONLY valid JSON. "
                    "Do not include any explanatory text, comments, or formatting before or after the JSON. "
                    "The response must start and end with valid JSON only.",
                ),
                (
                    "user",
                    "Extract skills from the following text:\n\n{text}\n\n{format_instructions}",
                ),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        skill_extraction_chain = skill_extraction_prompt | llm | parser

        extracted_skills = skill_extraction_chain.invoke({"text": text_to_analyze})
        return {"extractedSkills": extracted_skills["skills"]}

    except Exception as e:
        raise Exception(f"Failed to extract skills: {str(e)}")


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
                "rewrite_bullet": "/rewrite_bullet (POST)",
                "extract_skills": "/extract_skills (POST)",
                "suggest_upskilling": "/suggest_upskilling (POST)",
                "generate_pdf": "/generate_pdf (POST)",
                "generate_pdf_langchain": "/generate_pdf_langchain (POST)",
                "parse_resume_langchain": "/parse_resume_langchain (POST)",
                "generate_pdf_from_structured_data": "/generate_pdf_from_structured_data (POST)",
            },
            "langchain_features": {
                "unified_workflow": "Complete resume processing and PDF generation in one chain",
                "modular_chains": "Separate chains for parsing and PDF generation",
                "custom_parsers": "Custom output parsers for structured data and PDF generation",
                "error_handling": "Comprehensive error handling in LangChain workflows",
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

        # Extract skills from resume and job posting
        # Fix: Call the function directly instead of making HTTP requests
        resume_skills_data = extract_skills_from_text(parsed_resume_text)
        job_posting_skills_data = extract_skills_from_text(job_posting_text)

        resume_skills = set(resume_skills_data["extractedSkills"])
        job_posting_skills = set(job_posting_skills_data["extractedSkills"])

        # Identify skill gaps
        skill_gaps = list(job_posting_skills - resume_skills)
        matched_skills = list(job_posting_skills.intersection(resume_skills))

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
                "resumeSkills": list(resume_skills),
                "jobPostingSkills": list(job_posting_skills),
                "skillGaps": skill_gaps,
                "matchedSkills": matched_skills,
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


# Define a Pydantic model for structured skill extraction
class Skills(BaseModel):
    skills: list[str] = Field(description="List of skills extracted from the text.")


# Define a Pydantic model for structured resume data
class ResumeData(BaseModel):
    name: str = Field(description="Full name")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    location: str = Field(description="Location/City, State")
    summary: str = Field(description="Professional summary")
    experience: list[dict] = Field(description="List of work experience entries")
    education: list[dict] = Field(description="List of education entries")
    skills: list[str] = Field(description="List of skills")
    projects: list[dict] = Field(description="List of projects", default=[])
    certifications: list[dict] = Field(description="List of certifications", default=[])


# Custom LangChain Output Parser for PDF Generation
class PDFGenerationOutputParser(BaseOutputParser[Dict[str, Any]]):
    """Custom output parser that generates PDF and returns structured data."""

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the input text and generate PDF."""
        # This will be used in the chain, but the actual parsing happens in the chain
        return {"raw_text": text}

    def format(self, prompt: str) -> str:
        """Format the prompt for PDF generation."""
        return prompt


# Custom LangChain Output Parser for Resume Data
class ResumeDataOutputParser(BaseOutputParser[Dict[str, Any]]):
    """Custom output parser for structured resume data."""

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse structured resume data from text."""
        try:
            # Try to parse as JSON first
            import json

            return json.loads(text)
        except:
            # Fallback to basic parsing
            return {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "(555) 123-4567",
                "location": "City, State",
                "summary": text[:500] + "..." if len(text) > 500 else text,
                "experience": [],
                "education": [],
                "skills": [],
                "projects": [],
                "certifications": [],
            }

    def format(self, prompt: str) -> str:
        """Format the prompt for resume data extraction."""
        return prompt


@app.route("/extract_skills", methods=["POST"])
def extract_skills_endpoint():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "Missing text"}), 400

    text_to_analyze = data["text"]

    try:
        parser = JsonOutputParser(pydantic_object=Skills)

        skill_extraction_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at identifying and extracting technical and soft skills from text. "
                    "Extract a comprehensive list of distinct skills. You must respond with ONLY valid JSON. "
                    "Do not include any explanatory text, comments, or formatting before or after the JSON. "
                    "The response must start and end with valid JSON only.",
                ),
                (
                    "user",
                    "Extract skills from the following text:\n\n{text}\n\n{format_instructions}",
                ),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        skill_extraction_chain = skill_extraction_prompt | llm | parser

        extracted_skills = skill_extraction_chain.invoke({"text": text_to_analyze})
        return jsonify({"extractedSkills": extracted_skills["skills"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/suggest_upskilling", methods=["POST"])
def suggest_upskilling_endpoint():
    data = request.json
    if not data or "skillGaps" not in data or "jobDescription" not in data:
        return jsonify({"error": "Missing skill gaps or job description"}), 400

    skill_gaps = data["skillGaps"]
    job_description = data["jobDescription"]

    try:
        upskilling_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an AI career coach. Based on identified skill gaps for a job, "
                    "suggest a personalized upskilling path. Focus on what skills to learn and why they are important for the job. "
                    "Provide actionable advice and potential learning areas, but DO NOT recommend specific courses or platforms. "
                    "Keep the suggestions concise and encouraging.",
                ),
                (
                    "user",
                    "Identified Skill Gaps: {skill_gaps}\n\nJob Description:\n{job_description}\n\nSuggest an upskilling path to bridge these gaps for the given job. Focus on the 'what' and 'why', not specific course names.",
                ),
            ]
        )

        upskilling_chain = upskilling_prompt | llm | StrOutputParser()

        upskilling_suggestion = upskilling_chain.invoke(
            {"skill_gaps": ", ".join(skill_gaps), "job_description": job_description}
        )

        return jsonify({"upskillingSuggestion": upskilling_suggestion})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# LangChain Chains for PDF Generation Workflow


def create_resume_parsing_chain():
    """Create a LangChain chain for parsing resume text to structured data."""
    parser = JsonOutputParser(pydantic_object=ResumeData)

    resume_parsing_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at parsing resume text and extracting structured data. "
                "Extract the following information from the resume text and return it as valid JSON. "
                "If any information is not available, use appropriate defaults or empty values. "
                "For experience and education, create lists of dictionaries with relevant fields. "
                "You must respond with ONLY valid JSON. No explanatory text or comments.",
            ),
            (
                "user",
                "Parse this resume text and extract structured data:\n\n{resume_text}\n\n{format_instructions}",
            ),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    return resume_parsing_prompt | llm | parser


def create_pdf_generation_chain():
    """Create a LangChain chain for PDF generation."""

    # Custom function to generate PDF from structured data
    def generate_pdf_from_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF from structured data and return both PDF and data."""
        try:
            # Extract structured_data from inputs
            structured_data = inputs.get("structured_data", {})

            # If structured_data is an AIMessage, extract the content
            if hasattr(structured_data, "content"):
                import json

                try:
                    structured_data = json.loads(structured_data.content)
                except:
                    # If it's not JSON, use the content as is
                    structured_data = {"summary": structured_data.content}

            pdf_bytes = generate_resume_pdf(structured_data)
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            return {
                "success": True,
                "pdfBase64": pdf_base64,
                "structuredData": structured_data,
                "pdfSize": len(pdf_bytes),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "structuredData": inputs.get("structured_data", {}),
            }

    return RunnableLambda(generate_pdf_from_data)


def create_unified_resume_processing_chain():
    """Create a unified LangChain chain that processes resume text and generates PDF."""

    # Step 1: Parse resume text to structured data
    resume_parsing_chain = create_resume_parsing_chain()

    # Step 2: Generate PDF from structured data
    pdf_generation_chain = create_pdf_generation_chain()

    # Create the unified chain
    def process_resume_and_generate_pdf(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process resume text and generate PDF in one unified workflow."""
        resume_text = inputs.get("resume_text", "")

        try:
            # Step 1: Parse resume to structured data
            structured_data = resume_parsing_chain.invoke({"resume_text": resume_text})

            # Step 2: Generate PDF
            pdf_result = pdf_generation_chain.invoke(
                {"structured_data": structured_data}
            )

            return {
                "success": True,
                "structuredData": structured_data,
                "pdfBase64": pdf_result.get("pdfBase64", ""),
                "pdfSize": pdf_result.get("pdfSize", 0),
                "workflow": "langchain_unified",
            }

        except Exception as e:
            return {"success": False, "error": str(e), "workflow": "langchain_unified"}

    return RunnableLambda(process_resume_and_generate_pdf)


# Initialize the chains
resume_parsing_chain = create_resume_parsing_chain()
pdf_generation_chain = create_pdf_generation_chain()
unified_resume_chain = create_unified_resume_processing_chain()


def parse_resume_to_structured_data(resume_text: str) -> dict:
    """Parse resume text and extract structured data for PDF generation."""
    try:
        parser = JsonOutputParser(pydantic_object=ResumeData)

        resume_parsing_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at parsing resume text and extracting structured data. "
                    "Extract the following information from the resume text and return it as valid JSON. "
                    "If any information is not available, use appropriate defaults or empty values. "
                    "For experience and education, create lists of dictionaries with relevant fields. "
                    "You must respond with ONLY valid JSON. No explanatory text or comments.",
                ),
                (
                    "user",
                    "Parse this resume text and extract structured data:\n\n{resume_text}\n\n{format_instructions}",
                ),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        parsing_chain = resume_parsing_prompt | llm | parser
        structured_data = parsing_chain.invoke({"resume_text": resume_text})

        return structured_data
    except Exception as e:
        # Fallback to basic parsing if AI parsing fails
        return {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "(555) 123-4567",
            "location": "City, State",
            "summary": (
                resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
            ),
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
        }


def generate_resume_pdf(resume_data: dict) -> bytes:
    """Generate a professional PDF resume from structured data."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Get styles
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5,
    )

    normal_style = ParagraphStyle(
        "CustomNormal", parent=styles["Normal"], fontSize=11, spaceAfter=6
    )

    # Build the PDF content
    story = []

    # Header
    story.append(Paragraph(resume_data.get("name", "Resume"), title_style))

    # Contact information
    contact_info = []
    if resume_data.get("email"):
        contact_info.append(resume_data["email"])
    if resume_data.get("phone"):
        contact_info.append(resume_data["phone"])
    if resume_data.get("location"):
        contact_info.append(resume_data["location"])

    if contact_info:
        story.append(Paragraph(" | ".join(contact_info), normal_style))
        story.append(Spacer(1, 12))

    # Professional Summary
    if resume_data.get("summary"):
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(Paragraph(resume_data["summary"], normal_style))
        story.append(Spacer(1, 12))

    # Experience
    if resume_data.get("experience"):
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
        for exp in resume_data["experience"]:
            # Job title and company
            job_title = exp.get("title", "")
            company = exp.get("company", "")
            duration = exp.get("duration", "")

            if job_title or company:
                header_text = f"<b>{job_title}</b>"
                if company:
                    header_text += f" - {company}"
                if duration:
                    header_text += f" | {duration}"
                story.append(Paragraph(header_text, normal_style))

            # Job description
            description = exp.get("description", "")
            if description:
                story.append(Paragraph(description, normal_style))

            # Bullet points
            bullets = exp.get("bullets", [])
            for bullet in bullets:
                story.append(Paragraph(f"• {bullet}", normal_style))

            story.append(Spacer(1, 8))

    # Education
    if resume_data.get("education"):
        story.append(Paragraph("EDUCATION", section_style))
        for edu in resume_data["education"]:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")

            if degree or school:
                edu_text = f"<b>{degree}</b>"
                if school:
                    edu_text += f" - {school}"
                if year:
                    edu_text += f" | {year}"
                story.append(Paragraph(edu_text, normal_style))
        story.append(Spacer(1, 12))

    # Skills
    if resume_data.get("skills"):
        story.append(Paragraph("SKILLS", section_style))
        skills_text = ", ".join(resume_data["skills"])
        story.append(Paragraph(skills_text, normal_style))
        story.append(Spacer(1, 12))

    # Projects
    if resume_data.get("projects"):
        story.append(Paragraph("PROJECTS", section_style))
        for project in resume_data["projects"]:
            project_name = project.get("name", "")
            project_desc = project.get("description", "")

            if project_name:
                story.append(Paragraph(f"<b>{project_name}</b>", normal_style))
            if project_desc:
                story.append(Paragraph(project_desc, normal_style))
            story.append(Spacer(1, 6))

    # Certifications
    if resume_data.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", section_style))
        for cert in resume_data["certifications"]:
            cert_name = cert.get("name", "")
            cert_org = cert.get("organization", "")
            cert_date = cert.get("date", "")

            if cert_name:
                cert_text = f"<b>{cert_name}</b>"
                if cert_org:
                    cert_text += f" - {cert_org}"
                if cert_date:
                    cert_text += f" | {cert_date}"
                story.append(Paragraph(cert_text, normal_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


@app.route("/generate_pdf", methods=["POST"])
def generate_pdf_endpoint():
    """Generate a PDF resume from parsed resume text."""
    data = request.json
    if not data or "resumeText" not in data:
        return jsonify({"error": "Missing resume text"}), 400

    resume_text = data["resumeText"]

    try:
        # Parse resume text to structured data
        structured_data = parse_resume_to_structured_data(resume_text)

        # Generate PDF
        pdf_bytes = generate_resume_pdf(structured_data)

        # Convert to base64 for transmission
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return jsonify(
            {
                "success": True,
                "pdfBase64": pdf_base64,
                "structuredData": structured_data,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


@app.route("/generate_pdf_langchain", methods=["POST"])
def generate_pdf_langchain_endpoint():
    """Generate a PDF resume using LangChain chains."""
    data = request.json
    if not data or "resumeText" not in data:
        return jsonify({"error": "Missing resume text"}), 400

    resume_text = data["resumeText"]

    try:
        # Use the unified LangChain chain
        result = unified_resume_chain.invoke({"resume_text": resume_text})

        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify({"error": result.get("error", "Unknown error")}), 500

    except Exception as e:
        return (
            jsonify({"error": f"Failed to generate PDF with LangChain: {str(e)}"}),
            500,
        )


@app.route("/parse_resume_langchain", methods=["POST"])
def parse_resume_langchain_endpoint():
    """Parse resume text to structured data using LangChain."""
    data = request.json
    if not data or "resumeText" not in data:
        return jsonify({"error": "Missing resume text"}), 400

    resume_text = data["resumeText"]

    try:
        # Use the resume parsing chain
        structured_data = resume_parsing_chain.invoke({"resume_text": resume_text})
        return jsonify({"structuredData": structured_data})

    except Exception as e:
        return (
            jsonify({"error": f"Failed to parse resume with LangChain: {str(e)}"}),
            500,
        )


@app.route("/generate_pdf_from_structured_data", methods=["POST"])
def generate_pdf_from_structured_data_endpoint():
    """Generate PDF from structured resume data using LangChain."""
    data = request.json
    if not data or "structuredData" not in data:
        return jsonify({"error": "Missing structured data"}), 400

    structured_data = data["structuredData"]

    try:
        # Use the PDF generation chain
        result = pdf_generation_chain.invoke({"structured_data": structured_data})
        return jsonify(result)

    except Exception as e:
        return (
            jsonify(
                {"error": f"Failed to generate PDF from structured data: {str(e)}"}
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
