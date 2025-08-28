# backend/sample_data.py

import uuid
import json


def generate_sample_courses(num_courses: int = 10) -> list[dict]:
    """Generates a list of sample course dictionaries."""
    courses = []
    course_names = [
        "Introduction to Python Programming",
        "Advanced JavaScript for Web Development",
        "Machine Learning Fundamentals",
        "Deep Learning with TensorFlow",
        "Data Science with Python and R",
        "Cloud Computing with AWS",
        "DevOps Essentials",
        "Cybersecurity Basics",
        "Database Management with SQL",
        "Frontend Development with React and Next.js",
    ]
    course_descriptions = [
        "Learn the basics of Python, including data types, control flow, and functions. Perfect for beginners.",
        "Dive deep into modern JavaScript features, frameworks like React, and build dynamic web applications.",
        "Understand core machine learning concepts, algorithms, and practical applications using scikit-learn.",
        "Explore neural networks, convolutional networks, and recurrent networks using TensorFlow and Keras.",
        "Master data manipulation, analysis, and visualization using Python (Pandas, Matplotlib) and R.",
        "Get hands-on experience with Amazon Web Services (AWS) core services like EC2, S3, and Lambda.",
        "Learn continuous integration, continuous delivery, and infrastructure as code for efficient software delivery.",
        "Discover fundamental cybersecurity principles, network security, and common cyber threats.",
        "Gain proficiency in SQL for database design, querying, and management across various relational databases.",
        "Build modern, high-performance web applications using React, Next.js, and state management libraries.",
    ]
    course_skills = [
        ["Python", "Programming Basics", "Algorithms"],
        ["JavaScript", "React", "Next.js", "Web Development"],
        ["Machine Learning", "Python", "Scikit-learn", "Data Analysis"],
        ["Deep Learning", "TensorFlow", "Keras", "Neural Networks"],
        ["Data Science", "Python", "R", "Pandas", "Matplotlib"],
        ["AWS", "Cloud Computing", "EC2", "S3", "Lambda"],
        ["DevOps", "CI/CD", "Docker", "Kubernetes"],
        ["Cybersecurity", "Network Security", "Threat Analysis"],
        ["SQL", "Database Design", "Data Querying"],
        ["React", "Next.js", "Frontend Development", "UI/UX"],
    ]

    for i in range(num_courses):
        idx = i % len(course_names)
        course = {
            "id": str(uuid.uuid4()),
            "name": course_names[idx],
            "description": course_descriptions[idx],
            "url": f"https://example.com/courses/{idx+1}",
            "skills": course_skills[idx],
        }
        courses.append(course)
    return courses


if __name__ == "__main__":
    sample_courses = generate_sample_courses(15)  # Generate 15 courses
    for course in sample_courses:
        print(course)
