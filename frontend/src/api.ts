const teacher = () => localStorage.getItem("teacher") || "";
export const studentCode = () => localStorage.getItem("code") || "";

async function req<T = any>(path: string, opts: RequestInit = {}, who: "t" | "s" = "t"): Promise<T> {
  const h: Record<string, string> = {};
  if (who === "t") h.Authorization = "Bearer " + teacher(); else h["X-Student-Code"] = studentCode();
  if (opts.body && !(opts.body instanceof FormData)) h["Content-Type"] = "application/json";
  const r = await fetch("/api" + path, { ...opts, headers: h });
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}
const form = (files: FileList | File[]) => { const f = new FormData(); Array.from(files).forEach(x => f.append("files", x)); return f; };

export const api = {
  topics: () => req("/teacher/topics"),
  topic: (id: string) => req(`/teacher/topics/${id}`),
  verdict: (id: number, verdict: string) => req(`/teacher/topics/${id}/verdict`, { method: "POST", body: JSON.stringify({ verdict }) }),
  materials: () => req("/teacher/materials"),
  upload: (files: FileList) => req("/teacher/materials", { method: "POST", body: form(files) }),
  quiz: () => req("/teacher/quiz"),
  importQuiz: (file: File) => { const f = new FormData(); f.append("file", file); return req("/teacher/quiz/import", { method: "POST", body: f }); },
  login: (code: string) => req("/student/login", { method: "POST", body: JSON.stringify({ code }) }, "s"),
  sMaterials: () => req("/student/materials", {}, "s"),
  chat: (text: string, session_id: string) => req("/student/chat", { method: "POST", body: JSON.stringify({ text, session_id }) }, "s"),
  feedback: (message_id: number, value: string) => req("/student/feedback", { method: "POST", body: JSON.stringify({ message_id, value }) }, "s"),
};
