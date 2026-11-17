/** Hand-authored 24px stroke icons (no icon library). Decorative by default: aria-hidden. */
const PATHS: Record<string, string> = {
  overview: "M4 13h6V4H4zM14 20h6v-9h-6zM14 8h6V4h-6zM4 20h6v-3H4z",
  quiz: "M9 5h10M9 12h10M9 19h10M4.5 5h.01M4.5 12h.01M4.5 19h.01",
  files: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 13h6M9 17h4",
  settings: "M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6",
  back: "M19 12H5M11 18l-6-6 6-6",
  arrow: "M5 12h14M13 6l6 6-6 6",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4",
  upload: "M12 16V4M7 9l5-5 5 5M5 20h14",
  copy: "M9 9h10v11H9zM5 15V4h10",
  check: "M5 12.5l4.5 4.5L19 7.5",
  alert: "M12 8v5M12 16.5h.01M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 7.5h.01",
  send: "M5 12h13M12 5l7 7-7 7",
  logout: "M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5 5-5M5 12h11",
  plus: "M12 5v14M5 12h14",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  edit: "M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4",
  refresh: "M20 11a8 8 0 0 0-14.7-4.3L4 8M4 4v4h4M4 13a8 8 0 0 0 14.7 4.3L20 16M20 20v-4h-4",
  course: "M4 6.5A2.5 2.5 0 0 1 6.5 4H20v14H6.5A2.5 2.5 0 0 0 4 20.5zM4 20.5A2.5 2.5 0 0 1 6.5 18H20M9 8h7",
  users: "M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM20 20v-1.5a3.5 3.5 0 0 0-2.5-3.4M15.5 4.2a3.5 3.5 0 0 1 0 6.6",
  message: "M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.2A8 8 0 1 1 20 12z",
  lock: "M6 11h12v9H6zM8.5 11V8a3.5 3.5 0 0 1 7 0v3",
  eye: "M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  x: "M6 6l12 12M18 6 6 18",
  spark: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18",
  pdf: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M8.5 16v-4h1.5a1.2 1.2 0 0 1 0 2.4H8.5M13 12v4M13 12h2M13 14h1.5",
  slides: "M3 5h18v11H3zM12 16v4M8 20h8",
  doc: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M8.5 12h7M8.5 15.5h7M8.5 19h4",
  notebook: "M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6zM9 3v18M12.5 8h3.5M12.5 12h3.5",
  text: "M5 6h14M5 10h14M5 14h10M5 18h7",
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, label, className = "" }: { name: IconName | string; label?: string; className?: string }) {
  return <svg className={`icon ${className}`.trim()} viewBox="0 0 24 24" role={label ? "img" : undefined}
    aria-label={label} aria-hidden={label ? undefined : true} focusable="false"><path d={PATHS[name] || PATHS.files} /></svg>;
}

/** Icon for a material kind as returned by the API (PDF, PowerPoint, Word, Notebook, Markdown, Text). */
export function kindIcon(kindOrFilename: string): IconName {
  const value = kindOrFilename.toLowerCase();
  if (value.includes("pdf")) return "pdf";
  if (value.includes("power") || value.endsWith(".pptx")) return "slides";
  if (value.includes("word") || value.endsWith(".docx")) return "doc";
  if (value.includes("notebook") || value.endsWith(".ipynb")) return "notebook";
  return "text";
}
