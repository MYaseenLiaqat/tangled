const instructorToken = () => localStorage.getItem("instructor_token") || "";
const studentToken = () => localStorage.getItem("student_token") || "";

async function req<T = any>(path: string, opts: RequestInit = {}, token = instructorToken()): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(`/api/v1${path}`, { ...opts, headers: { ...headers, ...opts.headers } });
  if (!response.ok) throw new Error((await response.text()) || response.statusText);
  return response.json();
}

export const api = {
  register: (email: string, password: string) => req("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) => req("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  courses: () => req("/courses"),
  course: (id: string) => req(`/courses/${id}`),
  createCourse: (name: string, class_size?: number) => req("/courses", { method: "POST", body: JSON.stringify({ name, class_size }) }),
  updateCourse: (id: string, values: Record<string, unknown>) => req(`/courses/${id}`, { method: "PATCH", body: JSON.stringify(values) }),
  regenerateCode: (id: string) => req(`/courses/${id}/join-code/regenerate`, { method: "POST" }),
  topicsForCourse: (id: string) => req(`/courses/${id}/topics`),
  createTopic: (id: string, values: Record<string, string>) => req(`/courses/${id}/topics`, { method: "POST", body: JSON.stringify(values) }),
  updateTopic: (courseId: string, topicId: number, values: Record<string, string>) => req(`/courses/${courseId}/topics/${topicId}`, { method: "PATCH", body: JSON.stringify(values) }),
  deleteTopic: (courseId: string, topicId: number) => req(`/courses/${courseId}/topics/${topicId}`, { method: "DELETE" }),
  materialsForCourse: (id: string) => req(`/courses/${id}/materials`),
  uploadMaterials: (id: string, files: FileList) => {
    const form = new FormData();
    Array.from(files).forEach(file => form.append("files", file));
    return req(`/courses/${id}/materials`, { method: "POST", body: form });
  },
  deleteMaterial: (courseId: string, materialId: number) => req(`/courses/${courseId}/materials/${materialId}`, { method: "DELETE" }),
  joinInfo: (code: string) => req(`/student/join/${code}`, {}, ""),
  join: (code: string) => req("/student/join", { method: "POST", body: JSON.stringify({ code, consent: true }) }, ""),
  studentMaterials: () => req("/student/materials", {}, studentToken()),
  chat: (text: string, sessionId: string) => req("/student/chat", { method: "POST", body: JSON.stringify({ text, session_id: sessionId }) }, studentToken()),
  feedback: (messageId: number, value: string) => req("/student/feedback", { method: "POST", body: JSON.stringify({ message_id: messageId, value }) }, studentToken()),
  topics: (): Promise<any> => Promise.reject(new Error("Legacy topics page is disabled")),
  topic: (_id: string): Promise<any> => Promise.reject(new Error("Legacy topic page is disabled")),
  verdict: (_id: number, _value: string): Promise<any> => Promise.reject(new Error("Insights are disabled until a later phase")),
  materials: (): Promise<any> => Promise.reject(new Error("Legacy materials page is disabled")),
  upload: (_files: FileList): Promise<any> => Promise.reject(new Error("Legacy materials page is disabled")),
  quiz: (): Promise<any> => Promise.reject(new Error("Quiz is disabled until a later phase")),
  importQuiz: (_file: File): Promise<any> => Promise.reject(new Error("Quiz is disabled until a later phase")),
};
