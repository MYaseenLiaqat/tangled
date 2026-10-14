const token = () => localStorage.getItem("instructor_token") || "";

async function req<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { Authorization: `Bearer ${token()}` };
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
  topics: (): Promise<any> => Promise.reject(new Error("Topics are disabled until Phase 3")),
  topic: (_id: string): Promise<any> => Promise.reject(new Error("Topics are disabled until Phase 3")),
  verdict: (_id: number, _verdict: string): Promise<any> => Promise.reject(new Error("Topics are disabled until Phase 3")),
  materials: (): Promise<any> => Promise.reject(new Error("Materials are disabled until Phase 3")),
  upload: (_files: FileList): Promise<any> => Promise.reject(new Error("Materials are disabled until Phase 3")),
  quiz: (): Promise<any> => Promise.reject(new Error("Quiz is disabled until a later phase")),
  importQuiz: (_file: File): Promise<any> => Promise.reject(new Error("Quiz is disabled until a later phase")),
  sMaterials: (): Promise<any> => Promise.reject(new Error("Student join is disabled until Phase 4")),
  chat: (_text: string, _sessionId: string): Promise<any> => Promise.reject(new Error("Student chat is disabled until Phase 4")),
  feedback: (_messageId: number, _value: string): Promise<any> => Promise.reject(new Error("Student chat is disabled until Phase 4")),
};

export const studentCode = () => "";
