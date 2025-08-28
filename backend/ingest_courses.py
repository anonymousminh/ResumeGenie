import os
import pymysql
from dotenv import load_dotenv
from sample_data import generate_sample_courses
from embedding_utils import get_text_embedding
import json

# Load environment variables from .env file
load_dotenv()

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
            autocommit=True,  # Ensure changes are committed
            ssl={
                "ssl": {
                    "ssl_mode": "VERIFY_IDENTITY",
                }
            },
        )
        print("Successfully connected to TiDB Serverless!")
        return conn
    except Exception as e:
        print(f"Error connecting to TiDB: {e}")
        return None


def insert_course_data(conn, courses: list[dict]):
    """Inserts course data into the courses table, including embeddings."""
    if not conn:
        print("No database connection. Skipping data insertion.")
        return

    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO courses (id, name, description, url, skills, embedding, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, NOW())
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        description = VALUES(description),
        url = VALUES(url),
        skills = VALUES(skills),
        embedding = VALUES(embedding);
    """

    print(f"Attempting to insert {len(courses)} courses...")
    for course in courses:
        try:
            # Combine description and skills for embedding
            text_to_embed = f"{course['name']}. {course['description']}. Skills: {', '.join(course['skills'])}"
            embedding = get_text_embedding(text_to_embed)

            cursor.execute(
                insert_sql,
                (
                    course["id"],
                    course["name"],
                    course["description"],
                    course["url"],
                    json.dumps(course["skills"]),  # Store skills as JSON string
                    json.dumps(embedding),  # Store embedding as JSON string
                ),
            )
            print(f"Inserted/Updated course: {course['name']}")
        except Exception as e:
            print(f"Error inserting course {course['name']}: {e}")
            # Optionally, log the full traceback: import traceback; traceback.print_exc()
    cursor.close()
    print("Data ingestion complete.")


def verify_course_data(conn):
    """Verifies that course data is accessible and correct."""
    if not conn:
        print("No database connection. Cannot verify data.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, description, embedding FROM courses LIMIT 5;")
        rows = cursor.fetchall()
        print("\n--- Verifying inserted courses (first 5) ---")
        for row in rows:
            course_id, name, description, embedding_json = row
            print(f"ID: {course_id}, Name: {name}")
            print(f"  Description (partial): {description[:100]}...")
            # Verify embedding is a valid JSON array
            try:
                embedding_list = json.loads(embedding_json)
                print(f"  Embedding (first 5 dims): {embedding_list[:5]}...")
                print(f"  Embedding Dimension: {len(embedding_list)}")
            except json.JSONDecodeError:
                print(f"  Embedding: Invalid JSON for embedding")
            print("-" * 30)
    except Exception as e:
        print(f"Error verifying data: {e}")
    finally:
        cursor.close()


if __name__ == "__main__":
    # Ensure your .env has TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASSWORD, OPENAI_API_KEY
    # And that the 'courses' table exists in your TiDB cluster (from Day 5 schema)

    conn = connect_to_tidb()
    if conn:
        sample_courses = generate_sample_courses(
            10
        )  # Generate 10 courses for ingestion
        insert_course_data(conn, sample_courses)
        verify_course_data(conn)
        conn.close()
