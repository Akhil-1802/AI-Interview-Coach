const BASE = "http://localhost:8000";

export async function startInterview({ resumeText, resumePdf, jobDescription }) {
  const form = new FormData();
  form.append("job_description", jobDescription);
  if (resumePdf) form.append("resume_pdf", resumePdf);
  else form.append("resume_text", resumeText);

  const res = await fetch(`${BASE}/start`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json();
}

export async function submitAnswer({ threadId, answer }) {
  const res = await fetch(`${BASE}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, answer }),
  });
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json();
}

export async function endEarly({ threadId }) {
  const res = await fetch(`${BASE}/end-early`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId }),
  });
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json();
}
