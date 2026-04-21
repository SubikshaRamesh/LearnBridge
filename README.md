# 🚀 LearnBridge — AI-Powered Career Recommendation System

## 🧠 Overview
LearnBridge is an AI-based career assistant that analyzes resumes and job descriptions to:
- Calculate match scores 📊
- Identify missing skills ❌
- Recommend personalized learning paths 📚
- Suggest relevant courses 🎯

---

## ⚙️ Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTML, CSS, JavaScript
- **AI/NLP:** Sentence Transformers (MiniLM)
- **Database:** MySQL (AWS RDS)
- **Containerization:** Docker

---

## 🏗️ Features

- Upload or paste resume text
- Input job description and career goal
- AI-based skill matching using embeddings
- Skill gap analysis
- Course recommendations

---

## 🧠 How It Works

1. Extracts text from resume and job description  
2. Converts text into embeddings using Sentence Transformers  
3. Computes similarity between skills  
4. Identifies missing skills  
5. Recommends courses based on gaps  

---

## 🐳 Run with Docker

```bash
docker build -t learnbridge .
docker run -p 8000:8000 learnbridge
