const BASE = "/api";

export async function getCourses() {
  const res = await fetch(`${BASE}/courses`);
  if (!res.ok) throw new Error("Failed to load courses");
  return res.json();
}

export async function assessFiles(files) {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${BASE}/assess`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Assessment failed" }));
    throw new Error(err.detail || "Assessment failed");
  }
  return res.json();
}

export async function sendChat(message, sessionId) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    throw new Error(err.detail || "Chat failed");
  }
  return res.json();
}
