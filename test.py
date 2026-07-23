from workflow.agent import planner_node, topic_choose_node, interview_node, final_evaluation_node

state = {
    "resume": """Aryab Sharma

Email: aryan@example.com
Phone: +91 9876543210

SUMMARY
Final-year Computer Science student with experience building full-stack web
applications and AI-powered systems. Passionate about backend development,
machine learning, and distributed systems.

TECHNICAL SKILLS
Languages: Python, JavaScript, Java
Frameworks: React, FastAPI, Express.js, Node.js
Databases: MongoDB, PostgreSQL
Tools: Git, Docker, Linux
AI/ML: TensorFlow, LangChain, OpenCV, NumPy, Pandas

PROJECTS

AI Research Assistant
- Built a multi-agent research system using LangChain and FastAPI.
- Integrated Tavily Search API for web search.
- Generated structured research reports using LLMs.

Gaming
- Built a gaming platform using MERN Stack.
- Implemented JWT Authentication.
- Added real-time chat using Socket.IO.

EDUCATION
B.Tech Computer Science, XYZ University, CGPA: 8

CERTIFICATIONS
Machine Learning Specialization""",

    "job_description": """AI Engineer Intern

Responsibilities
- Build AI-powered applications using Python.
- Develop REST APIs using FastAPI.
- Design and deploy LLM applications.
- Build agentic workflows using LangGraph.
- Work with vector databases and RAG.
- Use Docker for containerization.
- Work with Redis for caching and message queues.
- Collaborate using Git.

Required Skills: Python, FastAPI, LangGraph, LangChain, Redis, Docker, PostgreSQL, Git, RAG, Vector Databases
Preferred Skills: AWS, Kubernetes, CI/CD""",

    # new fields
    "resume_projects": [],
    "asked_questions": [],
    "covered_topics": [],
    "weak_topics": [],
    "strong_topics": [],
    "candidate_claims": [],
    "difficulty_level": 1,
    "follow_up_mode": False,

    # existing fields
    "missing_skills": [],
    "strengths": [],
    "current_topic": "",
    "skills_covered": [],
    "current_question": "",
    "current_answer": "",
    "current_result": {},
    "score": 0,
    "interview_results": [
        {
            "topic": "LangChain",
            "question": "In your AI Research Assistant project you used LangChain — walk me through how you structured the multi-agent system and what challenges you faced.",
            "answer": "I used LangChain agents with tools like Tavily Search. Each agent had a specific role. The main challenge was managing agent state between steps.",
            "score": 7,
            "feedback": "Good practical answer. Could elaborate on state management strategy.",
            "technical_correctness": 7,
            "depth": 6,
            "communication": 8,
        },
        {
            "topic": "Redis",
            "question": "The JD requires Redis for caching and message queues. You haven't used it before — how would you approach adding Redis-based rate limiting to your FastAPI service?",
            "answer": "I would store request counts in Redis with a TTL key per user IP.",
            "score": 5,
            "feedback": "Correct approach but missing details on sliding window vs fixed window, atomic operations, and Redis data structures.",
            "technical_correctness": 5,
            "depth": 4,
            "communication": 6,
        },
        {
            "topic": "Docker",
            "question": "Explain the difference between a Docker image and a Docker container.",
            "answer": "A Docker image is the running instance and the container is the template.",
            "score": 3,
            "feedback": "Concepts are reversed. An image is the template; a container is a running instance.",
            "technical_correctness": 2,
            "depth": 3,
            "communication": 5,
        },
        {
            "topic": "System Design",
            "question": "How would you design the backend for PlayVerse to handle 100k concurrent users?",
            "answer": "I would use load balancers, horizontal scaling, and a CDN for static assets.",
            "score": 5,
            "feedback": "Good starting point. Missing database sharding, WebSocket scaling for chat, and caching strategy.",
            "technical_correctness": 5,
            "depth": 4,
            "communication": 6,
        },
        {
            "topic": "RAG",
            "question": "You haven't used RAG before. Explain how you would add document Q&A to your AI Research Assistant.",
            "answer": "I would embed documents and store them in a vector database, then retrieve relevant chunks and pass them to the LLM.",
            "score": 8,
            "feedback": "Solid understanding of RAG pipeline. Mentioning chunking strategy and reranking would strengthen the answer.",
            "technical_correctness": 8,
            "depth": 7,
            "communication": 8,
        },
    ],
    "final_result": {},
}

# Test planner
print("=== Testing planner_node ===")
new_state = planner_node(state)
state["missing_skills"] = new_state["missing_skills"]
state["strengths"] = new_state["strengths"]
state["resume_projects"] = new_state["resume_projects"]
print("Missing skills:", state["missing_skills"])
print("Strengths:", state["strengths"])
print("Resume projects:", [p["name"] for p in state["resume_projects"]])

# Test topic selection
print("\n=== Testing topic_choose_node ===")
new_state = topic_choose_node(state)
state["current_topic"] = new_state["current_topic"]
print("Selected topic:", state["current_topic"])

# Test final evaluation
print("\n=== Testing final_evaluation_node ===")
state["weak_topics"] = ["Docker", "Redis"]
state["strong_topics"] = ["RAG", "LangChain"]
new_state = final_evaluation_node(state)
state["final_result"] = new_state["final_result"]

import json
print(json.dumps(state["final_result"], indent=2))
