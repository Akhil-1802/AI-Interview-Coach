import os, sys, uuid, shutil
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command
from interview_agent import app as interview_app, final_evaluation_node
from PdfLoader import load_pdf

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INITIAL_STATE = lambda resume, jd: {
    "resume": resume, "job_description": jd,
    "resume_projects": [], "interview_results": [], "skills_covered": [],
    "missing_skills": [], "strengths": [], "asked_questions": [],
    "covered_topics": [], "weak_topics": [], "strong_topics": [],
    "candidate_claims": [], "current_question": "", "current_answer": "",
    "current_topic": "", "current_result": {}, "score": 0,
    "difficulty_level": 1, "follow_up_mode": False, "final_result": {},
}


def _run_step(payload, config):
    planner_info = None
    final_report = None
    interrupt_question = None

    for event in interview_app.stream(payload, config=config, stream_mode="updates"):
        for node, data in event.items():
            if node == "planner":
                planner_info = {
                    "missing_skills": data.get("missing_skills", []),
                    "strengths": data.get("strengths", []),
                }
            elif node == "final_evaluation":
                final_report = data.get("final_result", {})
            elif node == "__interrupt__":
                obj = data[0]
                val = obj.value if hasattr(obj, "value") else obj
                interrupt_question = val.get("current_question", "")

    snapshot = interview_app.get_state(config)
    values = snapshot.values
    return values, planner_info, final_report, interrupt_question


# ── /start ────────────────────────────────────────────────────────────────
@api.post("/start")
async def start(
    resume_text: str = Form(default=""),
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(default=None),
):
    resume = resume_text
    if resume_pdf:
        tmp = f"/tmp/{uuid.uuid4()}.pdf"
        with open(tmp, "wb") as f:
            shutil.copyfileobj(resume_pdf.file, f)
        resume = load_pdf(tmp)
        os.remove(tmp)

    if not resume.strip():
        raise HTTPException(400, "Resume is required")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    values, planner_info, final_report, question = _run_step(INITIAL_STATE(resume, job_description), config)

    return {
        "thread_id": thread_id,
        "planner_info": planner_info,
        "current_question": question,
        "current_topic": values.get("current_topic"),
        "difficulty_level": values.get("difficulty_level", 1),
        "asked_count": len(values.get("asked_questions", [])),
        "history": values.get("interview_results", []),
        "final_result": final_report,
        "stage": "report" if final_report else "interview",
    }


# ── /answer ───────────────────────────────────────────────────────────────
class AnswerRequest(BaseModel):
    thread_id: str
    answer: str


@api.post("/answer")
async def answer(req: AnswerRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    values, _, final_report, question = _run_step(Command(resume=req.answer), config)  # resume= is the interrupt key

    return {
        "thread_id": req.thread_id,
        "current_question": question,
        "current_topic": values.get("current_topic"),
        "difficulty_level": values.get("difficulty_level", 1),
        "asked_count": len(values.get("asked_questions", [])),
        "history": values.get("interview_results", []),
        "final_result": final_report,
        "stage": "report" if final_report else "interview",
    }


# ── /end-early ────────────────────────────────────────────────────────────
class EndRequest(BaseModel):
    thread_id: str


@api.post("/end-early")
async def end_early(req: EndRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    snapshot = interview_app.get_state(config)
    current_state = snapshot.values
    if not current_state.get("interview_results"):
        raise HTTPException(400, "No answers recorded yet")
    report = final_evaluation_node(current_state)
    return {
        "final_result": report["final_result"],
        "history": current_state.get("interview_results", []),
        "stage": "report",
    }


@api.get("/health")
def healthcheck():
    return {"status":"ok"}
@api.head("/health")
def health():
    return {"status":"ok"}

