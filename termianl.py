"""
Terminal runner for AI Technical Interview Copilot.
Run: python3 run_interview.py
"""
import sys
from langgraph.types import Command
from workflow.agent import app, final_evaluation_node

RESUME = """Arya Sharma
Email: aryan@example.com | Phone: +91 9876543210

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
Machine Learning Specialization"""

JOB_DESCRIPTION = """AI Engineer Intern

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
Preferred Skills: AWS, Kubernetes, CI/CD"""

INITIAL_STATE = {
    "resume": RESUME,
    "job_description": JOB_DESCRIPTION,
    "resume_projects": [],
    "interview_results": [],
    "skills_covered": [],
    "missing_skills": [],
    "strengths": [],
    "asked_questions": [],
    "covered_topics": [],
    "weak_topics": [],
    "strong_topics": [],
    "candidate_claims": [],
    "current_question": "",
    "current_answer": "",
    "current_topic": "",
    "current_result": {},
    "score": 0,
    "difficulty_level": 1,
    "follow_up_mode": False,
    "final_result": {},
}

CONFIG = {"configurable": {"thread_id": "interview-session-1"}}
DIVIDER = "─" * 60


def clr(text, code):
    return f"\033[{code}m{text}\033[0m"


def print_score_bar(score: int):
    filled = "█" * score
    empty = "░" * (10 - score)
    color = "92" if score >= 7 else "93" if score >= 5 else "91"
    print(f"\n  Score  : {clr(filled + empty, color)} {score}/10")


def print_final_report(report: dict):
    print(f"\n{'═' * 60}")
    print(clr("   FINAL INTERVIEW REPORT", "1"))
    print(f"{'═' * 60}")
    print(f"\n  Overall Score  : {clr(str(report.get('overall_score', 'N/A')) + '/10', '1')}")
    rec = report.get("hiring_recommendation", "N/A")
    rec_color = "92" if "Hire" in rec and "No" not in rec else "91"
    print(f"  Recommendation : {clr(rec, rec_color)}")
    print(f"  Confidence     : {report.get('confidence_level', 'N/A')}")

    print(f"\n{DIVIDER}\n  SUMMARY\n{DIVIDER}")
    print(f"  {report.get('summary', '')}")

    print(f"\n{DIVIDER}\n  STRENGTHS\n{DIVIDER}")
    for s in report.get("strengths", []):
        print(f"  {clr('✓', '92')} {s}")

    print(f"\n{DIVIDER}\n  WEAKNESSES\n{DIVIDER}")
    for w in report.get("weaknesses", []):
        print(f"  {clr('✗', '91')} {w}")

    print(f"\n{DIVIDER}\n  MOST IMPRESSIVE ANSWERS\n{DIVIDER}")
    for item in report.get("most_impressive_answers", []):
        print(f"  {clr('★', '93')} [{item.get('topic')}] {item.get('why')}")

    print(f"\n{DIVIDER}\n  WEAKEST ANSWERS\n{DIVIDER}")
    for item in report.get("weakest_answers", []):
        print(f"  {clr('✗', '91')} [{item.get('topic')}] {item.get('why')}")

    print(f"\n{DIVIDER}\n  LEARNING ROADMAP\n{DIVIDER}")
    for item in report.get("recommended_learning_roadmap", []):
        print(f"  {clr('→', '96')} {item.get('topic')}")
        print(f"    {item.get('resources')}\n")

    print(f"\n{DIVIDER}\n  FINAL FEEDBACK\n{DIVIDER}")
    print(f"  {report.get('final_feedback', '')}")
    print(f"\n{'═' * 60}\n")


EXIT_COMMANDS = {"exit", "quit", "done", "end", "stop"}


class EarlyExit(Exception):
    pass


def get_answer(question_number: int, question: str) -> str:
    print(f"\n{DIVIDER}")
    print(clr(f"  Question {question_number}", "1;96"))
    print(f"{DIVIDER}")
    print(f"\n  {clr(question, '1')}")
    print(clr("  (type 'exit' to end the interview early)\n", "2"))
    try:
        answer = input("  Your answer: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise EarlyExit
    if answer.lower() in EXIT_COMMANDS:
        raise EarlyExit
    return answer if answer else "(no answer provided)"


def run():
    print(f"\n{'═' * 60}")
    print(clr("   AI TECHNICAL INTERVIEW COPILOT", "1;94"))
    print(f"{'═' * 60}")
    print("\n  Analyzing resume and job description...\n")

    question_number = 0
    input_data = INITIAL_STATE  # first invocation uses full initial state

    while True:
        # Stream until the graph pauses (interrupt) or ends
        final_report = None
        interrupted = False
        interrupt_question = None
        last_score = None
        last_feedback = None

        for event in app.stream(input_data, config=CONFIG, stream_mode="updates"):
            for node, data in event.items():

                if node == "planner":
                    print(f"  Missing Skills : {clr(', '.join(data.get('missing_skills', [])), '91')}")
                    print(f"  Strengths      : {clr(', '.join(data.get('strengths', [])), '92')}")
                    print(f"\n  Starting interview...\n")

                elif node == "evaluation":
                    result = data.get("current_result", {})
                    last_score = data.get("score")
                    last_feedback = result.get("feedback", "")

                elif node == "final_evaluation":
                    final_report = data.get("final_result", {})

                elif node == "__interrupt__":
                    interrupt_question = event["__interrupt__"][0].value.get("current_question", "")
                    interrupted = True

        # Show evaluation feedback from the previous answer (if any)
        if last_score is not None:
            print_score_bar(last_score)
            print(f"  Feedback: {last_feedback}")

        # Interview finished
        if final_report:
            print_final_report(final_report)
            break

        # Graph hit an interrupt — ask the candidate
        if interrupted and interrupt_question:
            question_number += 1
            try:
                answer = get_answer(question_number, interrupt_question)
            except EarlyExit:
                _trigger_early_final()
                break
            # Resume the graph by passing the answer via Command
            input_data = Command(resume=answer)
        else:
            # Graph ended without final_evaluation (shouldn't happen)
            break


def _trigger_early_final():
    """Pull whatever results exist from the checkpointer and generate final report."""
    print(f"\n  {clr('Ending interview early...', '93')}")
    print("  Generating your report based on answers so far...\n")

    snapshot = app.get_state(CONFIG)
    current_state = snapshot.values

    if not current_state.get("interview_results"):
        print("  No answers recorded yet. Goodbye!\n")
        return

    report_state = final_evaluation_node(current_state)
    print_final_report(report_state["final_result"])


if __name__ == "__main__":
    run()
