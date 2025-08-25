# backend/main.py (updated to include parsing endpoint that fetches from S3)

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from parser_utils import parse_document  # Import the parsing utility

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


@app.route("/upload_resume", methods=["POST"])
def upload_resume_endpoint():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    resume_file_b64 = data.get("resumeFileBase64")
    resume_file_name = data.get("resumeFileName")
    resume_file_type = data.get("resumeFileType")  # Added file type
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
                "jobPostingText": job_posting_text,  # Pass job posting text back for now
                "resumeFileType": resume_file_type,  # Pass file type back
            }
        )
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/parse_s3_documents", methods=["POST"])
def parse_s3_documents_endpoint():
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

    try:
        # Extract bucket name and key from S3 URL
        # Assuming URL format: https://BUCKET_NAME.s3.REGION.amazonaws.com/KEY
        path_parts = s3_url.split("/")
        bucket_name_from_url = path_parts[2].split(".")[0]  # e.g., my-bucket
        s3_key = "/".join(path_parts[3:])  # e.g., resumes/my_resume.pdf

        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name_from_url, Key=s3_key)
        resume_bytes = response["Body"].read()

        # Parse the document
        parsed_resume_text = parse_document(resume_bytes, resume_file_type)

        return jsonify(
            {
                "parsedResumeText": parsed_resume_text,
                "parsedJobPostingText": job_posting_text,
            }
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return jsonify({"error": "File not found in S3"}), 404
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
