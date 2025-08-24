# backend/main.py (updated)

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

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
    job_posting_text = data.get("jobPostingText")

    if not resume_file_b64 or not resume_file_name or not job_posting_text:
        return jsonify({"error": "Missing resume file, name, or job posting text"}), 400

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
            }
        )
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
