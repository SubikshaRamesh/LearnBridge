from __future__ import annotations
import os
import re
import pandas as pd
import pymysql
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

# =========================
# DATABASE SETUP
# =========================

bootstrap_conn = pymysql.connect(
    host="learnbridge.cbya0mskedy7.ap-south-1.rds.amazonaws.com",
    user="admin",
    password="Subiksha",
    port=3306,
)
bootstrap_cursor = bootstrap_conn.cursor()
bootstrap_cursor.execute("CREATE DATABASE IF NOT EXISTS learnbridge")
bootstrap_conn.commit()
bootstrap_cursor.close()
bootstrap_conn.close()

conn = pymysql.connect(
    host="learnbridge.cbya0mskedy7.ap-south-1.rds.amazonaws.com",
    user="admin",
    password="Subiksha",
    database="learnbridge",
    port=3306,
)
cursor = conn.cursor()
print("Connected to RDS")

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume TEXT,
    goal VARCHAR(255),
    match_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
)
conn.commit()

# =========================
# FASTAPI APP
# =========================

app = FastAPI(title="LearnBridge - AI Career Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LOAD DATASET
# =========================

df = pd.read_csv("final_courses.csv")

for column in ["title", "skills", "level", "platform"]:
    df[column] = df[column].fillna("").astype(str)

df = df.head(500)

# =========================
# AI MODEL
# =========================

EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# =========================
# REQUEST MODEL
# =========================


class AnalyzeRequest(BaseModel):
    resume_text: str = ""
    job_description: str = ""
    goal: str | None = None


# =========================
# UTIL FUNCTIONS
# =========================


def normalize(text: str) -> str:
    text = text.lower().replace(",", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


KNOWN_SKILLS = {
    "python","java","sql","machine learning","deep learning","tensorflow","pytorch",
    "data science","fastapi","aws","docker","kubernetes","nlp","pandas","numpy",
    "statistics","cloud","azure","git","api","backend","frontend","html","css","js"
}


def extract_skills(text: str) -> set[str]:
    text = text.lower()
    found = set()
    for skill in KNOWN_SKILLS:
        if skill in text:
            found.add(skill)
    return found


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    vec = EMBEDDER.encode([a, b], convert_to_tensor=True)
    return util.cos_sim(vec[0], vec[1]).item()


def get_missing(user: set[str], job: set[str]) -> list[str]:
    return list(job - user)


def learning_path(skills: list[str]) -> list[str]:
    return [f"Step {i+1} -> Learn {s.title()}" for i, s in enumerate(skills)]

# =========================
# RECOMMENDER
# =========================


def recommend_courses(missing_skills, user_skills, top_n=5):
    results = []
    missing_set = set(missing_skills)

    for _, row in df.iterrows():
        course_skills = set(row["skills"].lower().split(";"))

        missing_overlap = len(course_skills & missing_set)
        user_overlap = len(course_skills & user_skills)

        score = (3 * missing_overlap) + user_overlap

        if missing_overlap > 0:
            results.append((score, row))

    results.sort(reverse=True, key=lambda x: x[0])

    output = []
    for score, row in results[:top_n]:
        course_skills = set(row["skills"].lower().split(";"))
        overlap = list(course_skills & missing_set)

        reason = f"Helps you improve {', '.join(overlap[:2])}" if overlap else "Relevant"

        output.append({
            "title": row["title"],
            "platform": row["platform"],
            "level": row["level"],
            "skills": row["skills"].split(";")[:3],
            "reason": reason,
        })

    return output

# =========================
# ROUTES
# =========================


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    user_skills = extract_skills(payload.resume_text)
    job_skills = extract_skills(payload.job_description)

    match_score = int(((similarity(payload.resume_text, payload.job_description) + 1) / 2) * 100)
    missing_skills = get_missing(user_skills, job_skills)
    learning = learning_path(missing_skills)
    courses = recommend_courses(missing_skills, user_skills)
    job_ready = len(missing_skills) == 0 and match_score > 70

    cursor.execute(
        "INSERT INTO analysis (resume, goal, match_score) VALUES (%s, %s, %s)",
        (payload.resume_text, payload.goal, match_score),
    )
    conn.commit()

    return {
        "match_score": match_score,
        "missing_skills": missing_skills,
        "learning_path": learning,
        "recommended_courses": courses,
        "job_ready": job_ready,
    }


@app.get("/data")
def get_data():
    cursor.execute("SELECT * FROM analysis")
    return cursor.fetchall()