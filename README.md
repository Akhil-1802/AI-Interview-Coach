# 🎯 AI Interview Coach

An AI-powered mock technical interviewer that reads your resume and a job description, then runs a personalized, adaptive Q&A session.

Built with **LangGraph** + **Mistral AI** on the backend and **React + Tailwind CSS** on the frontend, connected via a **FastAPI** REST API.

🚀 **Live Demo** — [https://interview-aicoach.netlify.app](https://interview-aicoach.netlify.app)

---

## Features

- **Resume-aware questions** — references your actual projects, tech stack, and experience
- **JD gap analysis** — surfaces matched strengths and missing skills before the interview starts
- **Adaptive difficulty** — adjusts question depth based on your performance (scale 1–5)
- **Smart topic routing** — prioritizes gaps, then projects, strengths, system design, and CS fundamentals
- **Follow-up probing** — weak answers trigger deeper questions on the same topic
- **Per-answer scoring** — immediate feedback on technical correctness, depth, and communication
- **Final assessment report** — overall score, hiring recommendation, strengths/weaknesses, and a learning roadmap
- **Early exit** — end anytime and still get a full report
- **PDF or text resume** — upload a PDF or paste plain text

---

## Architecture

The interview is modeled as a **LangGraph** state machine. Each answer is submitted via the API, which resumes the graph from its last checkpoint.

```mermaid
flowchart TD
    START([Start]) --> planner[Planner]
    planner --> topic[Topic Chooser]
    topic --> interview[Interview]
    interview -->|interrupt: wait for answer| evaluation[Evaluation]
    evaluation -->|score ≤ 6: follow-up| interview
    evaluation -->|score > 6: next topic| topic
    evaluation -->|no more topics| final[Final Evaluation]
    topic -->|max questions reached| final
    final --> END([End])
```

| Node | Role |
|------|------|
| **Planner** | Parses resume + JD; extracts strengths, missing skills, resume projects |
| **Topic Chooser** | Picks the next topic based on priority and what's already covered |
| **Interview** | Generates a contextual question, then interrupts to wait for the answer |
| **Evaluation** | Scores the answer, adjusts difficulty, routes to follow-up or next topic |
| **Final Evaluation** | Produces the complete hiring assessment report |

---

## Project Structure

```
AI-Interview-Coach/
├── README.md
├── docker-compose.yml       # Runs both backend and frontend
├── backend/
│   ├── interview_agent.py   # LangGraph graph, nodes, state definition
│   ├── main.py              # FastAPI app — /start, /answer, /end-early, /health
│   ├── PdfLoader.py         # PDF → text extraction
│   ├── requirement.txt      # Python dependencies
│   ├── .env                 # API keys (not committed)
│   └── Dockerfile
└── frontend/
    ├── index.html
    ├── package.json
    ├── dockerfile
    └── src/
        ├── main.jsx
        ├── index.css         # Tailwind import
        ├── App.jsx           # UI: setup → interview → report
        └── api.js            # Fetch client for FastAPI
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Mistral AI API key | [Get one here](https://console.mistral.ai/) |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Akhil-1802/AI-Interview-Coach.git
cd AI-Interview-Coach
```

### 2. Backend

```bash
cd backend
pip install -r requirement.txt
```

Create a `.env` file inside `backend/`:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running Locally

Open two terminals from the project root:

```bash
# Terminal 1 — FastAPI backend
uvicorn backend.main:api --reload --port 8000

# Terminal 2 — React dev server
cd frontend
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

> The frontend talks to the backend at `http://localhost:8000`. Make sure both are running.

---

## Running with Docker

Runs both backend and frontend together from the project root:

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Backend API | [http://localhost:8000](http://localhost:8000) |
| Frontend | [http://localhost:5173](http://localhost:5173) |

> Make sure `backend/.env` exists with your `MISTRAL_API_KEY` before running.

---

## API Reference

All endpoints are served at `http://localhost:8000`.

### `POST /start`

Start a new interview session.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_description` | string | ✅ | The target job description |
| `resume_text` | string | one of | Plain text resume |
| `resume_pdf` | file | one of | PDF resume upload |

**Response**

```json
{
  "thread_id": "uuid",
  "planner_info": { "strengths": [], "missing_skills": [] },
  "current_question": "...",
  "current_topic": "...",
  "difficulty_level": 1,
  "asked_count": 1,
  "history": [],
  "final_result": null,
  "stage": "interview"
}
```

---

### `POST /answer`

Submit an answer and get the next question (or final report).

**Request** — `application/json`

```json
{ "thread_id": "uuid", "answer": "Your answer here" }
```

**Response** — same shape as `/start`. When the interview ends, `stage` becomes `"report"` and `final_result` is populated.

---

### `POST /end-early`

Stop the interview and generate a report from answers collected so far.

**Request** — `application/json`

```json
{ "thread_id": "uuid" }
```

**Response**

```json
{
  "final_result": { ... },
  "history": [ ... ],
  "stage": "report"
}
```

---

### `GET /health`

```json
{ "status": "ok" }
```

---

## How It Works

### Topic priority

Questions are drawn in this order until all topics are covered or the session limit is reached:

1. Skills in the JD but **missing** from the resume
2. **Projects** listed on the resume
3. **Matched strengths** (skills in both resume and JD)
4. **System design** (distributed systems, scalability, API design, …)
5. **CS fundamentals** (data structures, algorithms, OS, networking, …)

### Difficulty levels

| Level | Style |
|-------|-------|
| 1 | Conceptual / definition |
| 2 | Practical use-case |
| 3 | Project-specific implementation |
| 4 | Scenario, tradeoff, or debugging |
| 5 | System design / architecture |

- Score **≥ 7** → difficulty goes up, topic marked covered, move to next topic
- Score **≤ 6** → difficulty goes down, follow-up question on the same topic

### Final report

- Overall score (1–10)
- Hiring recommendation: `Strong Hire` / `Hire` / `No Hire` / `Strong No Hire`
- Confidence level
- Strengths and weaknesses
- Most impressive and weakest answers
- Recommended learning roadmap
- Detailed written feedback

---

## Configuration

Overridable via `.env` in `backend/`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MISTRAL_API_KEY` | — | Required — your Mistral API key |
| `PASSING_SCORE` | `6` | Minimum score to advance to the next topic |
| `MAX_QUESTIONS` | `15` | Maximum questions per session |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Mistral AI (`mistral-small-latest`) via LangChain |
| Orchestration | LangGraph (StateGraph, interrupts, MemorySaver) |
| API | FastAPI + Uvicorn |
| UI | React 19 + Tailwind CSS v4 + Vite |
| PDF parsing | PyPDF via LangChain Community |
| Config | python-dotenv |

---

## License

This project is open source. Add a license file if you plan to distribute it formally.

---

## Author

**Akhil** — [GitHub](https://github.com/Akhil-1802)
