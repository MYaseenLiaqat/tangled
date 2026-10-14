export function friendlyError(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (error instanceof Error) {
    try {
      const parsed = JSON.parse(error.message);
      if (typeof parsed.detail === "string") return parsed.detail;
      if (Array.isArray(parsed.detail)) return parsed.detail.map((item: any) => item.msg || "Invalid input").join(", ");
    } catch {
      if (error.message && !error.message.startsWith("{")) return error.message;
    }
  }
  return fallback;
}
