from langgraph.graph import StateGraph, START, END
from langchain_mistralai import ChatMistralAI
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict, Annotated, Optional
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
from PdfLoader import load_pdf

PASSING_SCORE = 6
MAX_QUESTIONS = 10

llm = ChatMistralAI(model="mistral-small-latest", temperature=0.5)


def addList(old: list, updated: list) -> list:
    return old + updated


class Evaluation(TypedDict):
    topic: str
    question: str
    answer: str
    score: int
    feedback: str
    technical_correctness: int
    depth: int
    communication: int


class InterviewState(TypedDict):
    resume: str
    job_description: str
    resume_projects: list
    interview_results: Annotated[list[Evaluation], addList]
    skills_covered: Annotated[list, addList]
    missing_skills: Annotated[list, addList]
    strengths: Annotated[list, addList]
    asked_questions: Annotated[list, addList]
    covered_topics: Annotated[list, addList]
    weak_topics: Annotated[list, addList]
    strong_topics: Annotated[list, addList]
    candidate_claims: Annotated[list, addList]
    current_question: str
    current_answer: str
    current_topic: str
    current_result: dict
    score: int
    difficulty_level: int
    follow_up_mode: bool
    final_result: dict


def planner_node(state: InterviewState):
    prompt = f"""
You are an AI Resume and Job Description Analyzer.

Given the candidate's resume and job description:
1. List skills present in JD AND resume -> strengths
2. List skills in JD but NOT in resume -> missing_skills
3. List all projects from the resume with their key technologies -> resume_projects

Candidate Resume:
{state["resume"]}

Job Description:
{state["job_description"]}

Return ONLY valid JSON:
{{
    "strengths": ["Skill 1", "Skill 2"],
    "missing_skills": ["Skill 3", "Skill 4"],
    "resume_projects": [
        {{"name": "Project Name", "technologies": ["Tech1", "Tech2"], "description": "brief description"}}
    ]
}}
"""
    chain = llm | JsonOutputParser()
    response = chain.invoke(prompt)
    return {
        "missing_skills": response.get("missing_skills", []),
        "strengths": response.get("strengths", []),
        "resume_projects": response.get("resume_projects", []),
    }


TOPIC_PRIORITY = [
    "missing_skills",
    "resume_projects",
    "strengths",
    "system_design",
    "cs_fundamentals",
]

SYSTEM_DESIGN_TOPICS = ["System Design", "Distributed Systems", "Scalability", "API Design"]
CS_FUNDAMENTALS = ["Data Structures", "Algorithms", "Operating Systems", "Networking"]


def topic_choose_node(state: InterviewState):
    covered = set(state.get("covered_topics", []))
    total_asked = len(state.get("asked_questions", []))

    if total_asked >= MAX_QUESTIONS:
        return {"current_topic": None}

    for skill in state.get("missing_skills", []):
        if skill not in covered:
            return {"current_topic": skill, "follow_up_mode": False}

    for project in state.get("resume_projects", []):
        topic = f"Project: {project['name']}"
        if topic not in covered:
            return {"current_topic": topic, "follow_up_mode": False}

    for skill in state.get("strengths", []):
        if skill not in covered:
            return {"current_topic": skill, "follow_up_mode": False}

    for topic in SYSTEM_DESIGN_TOPICS:
        if topic not in covered:
            return {"current_topic": topic, "follow_up_mode": False}

    for topic in CS_FUNDAMENTALS:
        if topic not in covered:
            return {"current_topic": topic, "follow_up_mode": False}

    return {"current_topic": None, "follow_up_mode": False}


INTERVIEWER_SYSTEM_PROMPT = """
You are a Senior Technical Interviewer at a top tech company (Google, Amazon, Microsoft, Atlassian).

Your interview style:
- Ask ONE focused question per turn.
- Reference the candidate's resume projects and experience when relevant.
- Never ask generic definitional questions like "What is Python?" or "What is Docker?" unless the candidate is extremely weak.
- Prefer: scenario-based, experience-based, project-based, tradeoff, debugging, architecture, and "why" questions.
- Match difficulty to the current difficulty level (1=definition, 2=use-case, 3=project-specific, 4=scenario/tradeoff, 5=system-design/architecture).
- Do NOT repeat any previously asked question.
- Do NOT provide hints or answers.
- Return ONLY the interview question -- no preamble, no explanation.
"""


def _build_interview_prompt(state: InterviewState) -> str:
    topic = state["current_topic"]
    difficulty = state.get("difficulty_level", 1)
    follow_up = state.get("follow_up_mode", False)
    asked = state.get("asked_questions", [])
    results = state.get("interview_results", [])
    resume_projects = state.get("resume_projects", [])
    weak_topics = state.get("weak_topics", [])
    candidate_claims = state.get("candidate_claims", [])

    project_context = ""
    if topic.startswith("Project:"):
        project_name = topic.replace("Project:", "").strip()
        for p in resume_projects:
            if p["name"] == project_name:
                project_context = f"\nProject details: {p['description']}. Technologies used: {', '.join(p['technologies'])}."
                break

    last_qa = ""
    if follow_up and results:
        last = results[-1]
        last_qa = f"\nPrevious question: {last['question']}\nCandidate answered: {last['answer']}\nScore: {last['score']}/10\n"
        last_qa += "Generate a follow-up that probes deeper -- do NOT repeat the same question."

    asked_str = "\n".join(f"- {q}" for q in asked[-10:]) if asked else "None"
    claims_str = "\n".join(f"- {c}" for c in candidate_claims[-5:]) if candidate_claims else "None"

    difficulty_guide = {
        1: "Ask a conceptual/definition question (only if candidate seems weak).",
        2: "Ask about a practical use-case or when they would use this.",
        3: "Ask about their specific project experience or implementation details.",
        4: "Ask a scenario, tradeoff, or debugging question.",
        5: "Ask a system design or architecture question.",
    }

    return f"""
Current Topic: {topic}{project_context}
Difficulty Level: {difficulty}/5 -- {difficulty_guide.get(difficulty, difficulty_guide[3])}
Candidate Resume Summary: {state["resume"][:800]}
Candidate Strengths: {', '.join(state.get("strengths", []))}
Missing Skills: {', '.join(state.get("missing_skills", []))}
Weak Topics So Far: {', '.join(weak_topics) if weak_topics else 'None'}
Interesting Claims by Candidate: {claims_str}
{last_qa}
Previously Asked Questions (DO NOT repeat):
{asked_str}

Generate ONE interview question for the topic above.
"""


def interview_node(state: InterviewState):
    topic = state["current_topic"]

    if topic is None:
        return {"current_question": None}

    prompt = _build_interview_prompt(state)
    response = llm.invoke([
        ("system", INTERVIEWER_SYSTEM_PROMPT),
        ("human", prompt)
    ])
    question = response.content.strip()

    answer = interrupt({"current_question": question})

    return {
        "current_question": question,
        "current_answer": answer,
        "asked_questions": [question],
    }


EVALUATION_SYSTEM_PROMPT = """
You are a Senior Technical Interviewer evaluating a candidate's answer.

Score each dimension from 1-10:
- technical_correctness: Is the answer factually correct?
- depth: Does the candidate show deep understanding beyond surface level?
- communication: Is the explanation clear and structured?
- practical_experience: Does the answer reflect real hands-on experience?

overall score = weighted average: (technical_correctness*0.4 + depth*0.3 + communication*0.2 + practical_experience*0.1)
Round overall score to nearest integer.

Also extract any interesting technical claims the candidate made (for follow-up questions).

Return ONLY valid JSON:
{
    "score": 7,
    "technical_correctness": 8,
    "depth": 6,
    "communication": 7,
    "practical_experience": 7,
    "feedback": "Constructive feedback here.",
    "candidate_claims": ["Candidate mentioned using Redis for pub/sub in their project"]
}
"""


def evaluation_node(state: InterviewState):
    question = state["current_question"]

    if question is None:
        return {"score": -1}

    prompt = f"""
Topic: {state["current_topic"]}
Question: {state["current_question"]}
Candidate Answer: {state["current_answer"]}
"""
    chain = llm | JsonOutputParser()
    result = chain.invoke([
        ("system", EVALUATION_SYSTEM_PROMPT),
        ("human", prompt)
    ])

    score = result["score"]
    topic = state["current_topic"]

    evaluation: Evaluation = {
        "topic": topic,
        "question": question,
        "answer": state["current_answer"],
        "score": score,
        "feedback": result["feedback"],
        "technical_correctness": result.get("technical_correctness", score),
        "depth": result.get("depth", score),
        "communication": result.get("communication", score),
    }

    current_difficulty = state.get("difficulty_level", 1)
    new_difficulty = min(5, current_difficulty + 1) if score >= 7 else max(1, current_difficulty - 1)

    updates = {
        "current_result": {"score": score, "feedback": result["feedback"]},
        "interview_results": [evaluation],
        "score": score,
        "difficulty_level": new_difficulty,
        "candidate_claims": result.get("candidate_claims", []),
    }

    if score <= 5:
        updates["weak_topics"] = [topic]
    elif score >= 7:
        updates["strong_topics"] = [topic]

    if score > PASSING_SCORE:
        updates["covered_topics"] = [topic]
        updates["skills_covered"] = [topic]

    return updates


def router(state: InterviewState):
    score = state["score"]
    if score == -1:
        return "final_evaluation"
    if score <= PASSING_SCORE:
        return "interview"
    return "topic"


FINAL_EVALUATION_PROMPT = """
You are a Senior Technical Interviewer writing a post-interview assessment report.

Return ONLY valid JSON:
{
    "overall_score": 7,
    "summary": "Overall performance summary.",
    "strengths": ["Strength 1", "Strength 2"],
    "weaknesses": ["Weakness 1", "Weakness 2"],
    "most_impressive_answers": [
        {"topic": "...", "question": "...", "why": "..."}
    ],
    "weakest_answers": [
        {"topic": "...", "question": "...", "why": "..."}
    ],
    "recommended_learning_roadmap": [
        {"topic": "...", "resources": "..."}
    ],
    "hiring_recommendation": "Strong Hire | Hire | No Hire | Strong No Hire",
    "confidence_level": "High | Medium | Low",
    "final_feedback": "Detailed constructive feedback."
}

Rules:
- overall_score: integer 1-10.
- hiring_recommendation must be one of: Strong Hire, Hire, No Hire, Strong No Hire.
- Base everything on the actual interview results provided.
- Be specific -- reference actual questions and answers.
"""


def final_evaluation_node(state: InterviewState):
    results_text = "\n\n".join(
        f"Topic: {r['topic']}\nQ: {r['question']}\nA: {r['answer']}\nScore: {r['score']}/10\nFeedback: {r['feedback']}"
        for r in state["interview_results"]
    )

    prompt = [
        ("system", FINAL_EVALUATION_PROMPT),
        ("human", f"""
Interview Results:
{results_text}

Candidate Strengths Identified: {', '.join(state.get("strong_topics", []))}
Candidate Weak Areas: {', '.join(state.get("weak_topics", []))}
Missing Skills from JD: {', '.join(state.get("missing_skills", []))}

Generate the final interview assessment report.
""")
    ]
    chain = llm | JsonOutputParser()
    result = chain.invoke(prompt)
    return {"final_result": result}


graph = StateGraph(InterviewState)

graph.add_node("planner", planner_node)
graph.add_node("topic", topic_choose_node)
graph.add_node("interview", interview_node)
graph.add_node("evaluation", evaluation_node)
graph.add_node("final_evaluation", final_evaluation_node)

graph.add_edge(START, "planner")
graph.add_edge("planner", "topic")
graph.add_edge("topic", "interview")
graph.add_edge("interview", "evaluation")
graph.add_conditional_edges("evaluation", router)
graph.add_edge("final_evaluation", END)

memory = MemorySaver()
app = graph.compile(checkpointer=memory, interrupt_before=[])
