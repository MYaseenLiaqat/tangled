export type Course = { id: number; name: string; join_code: string; join_link: string; joining_open: boolean; class_size?: number | null };
export type TopicCard = { id: number; name: string; module?: string; share: number; confidence: string | null; students_confused: number | string; confusion_messages: number | string; status?: string; signals: string[]; evidence_phrases: string[] };
export type TopicSummary = { summary: { questions: number | string; students_asking: number | string; enrolled: number | string; needs_attention: number }; flagged: TopicCard[]; not_flagged: { id: number; name: string; reason: string }[] };
export type TopicDetail = { id: number; name: string; module?: string; confidence: string | null; tier: string; status: string | null; stats: Record<string, number | string | null>; share: number; share_lower: number; signals: string[]; groups: { title: string; count: number | string; evidence_phrases: string[] }[]; not_counted_evidence: string[] };
export type QuizRow = { item: string; topic: string; correct_rate: number; responses: number; options: Record<string, number>; top_wrong: string | null };
export type Material = { id: number; filename: string; kind: string; size_kb: number; chunks: number; status: string; error: string };
export type Topic = { id: number; name: string; module_label: string; description: string; key: string };
export type TopicListItem = { id: number; name: string; module_label: string; description: string };
export type QuizImport = { imported: number; unmatched_concepts: { row: number; concept: string }[] };
type StudentMaterial = { id: number; filename: string; status: string; file_url?: string };
type StudentMessage = { message_id: number; question?: string; answer?: string; feedback?: string };
type JoinInfo = { name: string };

const instructorToken = () => localStorage.getItem("instructor_token") || "";
async function req<T>(path: string, opts: RequestInit = {}, token = instructorToken()): Promise<T> {
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
  if (opts.body && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(`/api/v1${path}`, { ...opts, headers: { ...headers, ...opts.headers } });
  if (!response.ok) throw new Error((await response.text()) || response.statusText);
  return response.json() as Promise<T>;
}

export function friendlyError(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (!(error instanceof Error)) return fallback;
  try {
    const parsed: unknown = JSON.parse(error.message);
    if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
      const detail = (parsed as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) return detail.map(item => typeof item === "object" && item !== null && "msg" in item ? String(item.msg) : "Invalid input").join(", ");
    }
  } catch { /* use the plain message below */ }
  return error.message && !error.message.startsWith("{") ? error.message : fallback;
}

export const api = {
  register: (email: string, password: string) => req<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) => req<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  courses: () => req<Course[]>("/courses"),
  course: (id: string) => req<Course>(`/courses/${id}`),
  createCourse: (name: string, class_size?: number) => req<Course>("/courses", { method: "POST", body: JSON.stringify({ name, class_size }) }),
  updateCourse: (id: string, values: Record<string, unknown>) => req<Course>(`/courses/${id}`, { method: "PATCH", body: JSON.stringify(values) }),
  regenerateCode: (id: string) => req<Course>(`/courses/${id}/join-code/regenerate`, { method: "POST" }),
  insights: (id: string) => req<TopicSummary>(`/courses/${id}/insights`),
  topic: (courseId: string, topicId: string) => req<TopicDetail>(`/courses/${courseId}/topics/${topicId}/insights`),
  verdict: (courseId: string, topicId: number, verdict: "addressed" | "false_alarm") => req<{ ok: boolean }>(`/courses/${courseId}/topics/${topicId}/verdict`, { method: "POST", body: JSON.stringify({ verdict }) }),
  topicsForCourse: (id: string) => req<Topic[] | TopicSummary>(`/courses/${id}/topics`),
  topicList: (id: string) => req<TopicListItem[]>(`/courses/${id}/topic-list`),
  createTopic: (id: string, values: { name: string; module_label: string; description: string }) => req<Topic>(`/courses/${id}/topics`, { method: "POST", body: JSON.stringify(values) }),
  updateTopic: (courseId: string, topicId: number, values: Partial<{ name: string; module_label: string; description: string }>) => req<Topic>(`/courses/${courseId}/topics/${topicId}`, { method: "PATCH", body: JSON.stringify(values) }),
  deleteTopic: (courseId: string, topicId: number) => req<{ ok: boolean }>(`/courses/${courseId}/topics/${topicId}`, { method: "DELETE" }),
  quiz: (id: string) => req<QuizRow[]>(`/courses/${id}/quiz`),
  importQuiz: (id: string, file: File) => { const form = new FormData(); form.append("file", file); return req<QuizImport>(`/courses/${id}/quiz/import`, { method: "POST", body: form }); },
  materialsForCourse: (id: string) => req<Material[]>(`/courses/${id}/materials`),
  uploadMaterials: (id: string, files: FileList) => { const form = new FormData(); Array.from(files).forEach(file => form.append("files", file)); return req<Material[]>(`/courses/${id}/materials`, { method: "POST", body: form }); },
  deleteMaterial: (courseId: string, materialId: number) => req<{ ok: boolean }>(`/courses/${courseId}/materials/${materialId}`, { method: "DELETE" }),
  joinInfo: (code: string) => req<JoinInfo>(`/student/join/${code}`, {}, ""),
  join: (code: string) => req<{ access_token: string }>("/student/join", { method: "POST", body: JSON.stringify({ code, consent: true }) }, ""),
  studentMaterials: () => req<StudentMaterial[]>("/student/materials", {}, localStorage.getItem("student_token") || ""),
  chat: (text: string, sessionId: string) => req<StudentMessage>("/student/chat", { method: "POST", body: JSON.stringify({ text, session_id: sessionId }) }, localStorage.getItem("student_token") || ""),
  feedback: (messageId: number, value: string) => req<{ ok: boolean }>("/student/feedback", { method: "POST", body: JSON.stringify({ message_id: messageId, value }) }, localStorage.getItem("student_token") || ""),
  studentMessages: () => req<StudentMessage[]>("/student/messages", {}, localStorage.getItem("student_token") || ""),
  materials: () => Promise.reject<Material[]>(new Error("Select a course to view materials.")),
  upload: (_files: FileList) => Promise.reject<Material[]>(new Error("Select a course to upload materials.")),
};
