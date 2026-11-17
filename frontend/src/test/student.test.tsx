import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Consent from "../pages/Consent";
import Student from "../pages/Student";
import { api } from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    api: {
      studentMaterials: vi.fn(),
      studentMessages: vi.fn(),
      chat: vi.fn(),
      feedback: vi.fn(),
    },
  };
});

describe("student citations", () => {
  beforeEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.mocked(api.studentMaterials).mockResolvedValue([]);
    vi.mocked(api.studentMessages).mockResolvedValue([]);
  });

  afterEach(() => cleanup());

  it("renders valid source names and sections", async () => {
    vi.mocked(api.studentMessages).mockResolvedValue([{
      message_id: 1,
      question: "What is a vector?",
      answer: "A vector is described here [1].",
      sources: [{ n: 1, material: "notes.pdf", section: "p. 2" }],
    }]);

    render(<Student />);

    expect(await screen.findByRole("list")).toHaveTextContent("notes.pdf");
    expect(screen.getByRole("list")).toHaveTextContent("p. 2");
    expect(screen.getByText(/A vector is described here/)).toBeInTheDocument();
    expect(screen.getByText("[1]")).toBeInTheDocument();
  });

  it("renders an answer without a source section when sources are empty", async () => {
    vi.mocked(api.studentMessages).mockResolvedValue([{
      message_id: 2,
      question: "Unknown",
      answer: "I could not find that in the materials.",
      sources: [],
    }]);

    render(<Student />);

    expect(await screen.findByText("I could not find that in the materials.")).toBeInTheDocument();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();
  });

  it("does not render unresolved citation references", async () => {
    vi.mocked(api.studentMessages).mockResolvedValue([{
      message_id: 3,
      question: "Question",
      answer: "Supported [1], unresolved [2].",
      sources: [{ n: 1, material: "notes.txt", section: "text" }],
    }]);

    render(<Student />);

    expect(await screen.findByText(/Supported/)).toBeInTheDocument();
    expect(screen.getByRole("list")).toHaveTextContent("notes.txt");
    expect(screen.getByRole("list")).toHaveTextContent("text");
    expect(screen.queryByText("[2]")).not.toBeInTheDocument();
  });

  it("makes the approved consent information accessible", () => {
    render(<MemoryRouter initialEntries={["/consent/ABC123"]}><Routes><Route path="/consent/:code" element={<Consent />} /></Routes></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Before you join" })).toBeInTheDocument();
    expect(screen.getByText("We do not collect your name or email.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Return to join" })).toHaveAttribute("href", "/join/ABC123");
  });
});

describe("answer formatting", () => {
  beforeEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.mocked(api.studentMaterials).mockResolvedValue([]);
  });

  it("renders markdown lists and bold text instead of raw symbols", async () => {
    vi.mocked(api.studentMessages).mockResolvedValue([{
      message_id: 3,
      question: "Learning rate?",
      answer: "The learning rate sets the step size [1].\n\n- If it is **too large**, the loss diverges [1].\n- If it is too small, training is slow [9].\n\n<img src=x onerror=alert(1)>",
      sources: [{ n: 1, material: "notes.pdf", section: "p. 1" }],
    }]);

    const { container } = render(<Student />);

    expect(await screen.findByText("too large")).toBeInTheDocument();
    expect(screen.getByText("too large").tagName).toBe("STRONG");
    expect(container.querySelectorAll(".answer li")).toHaveLength(2);
    expect(container.querySelector(".answer")?.textContent).not.toContain("**");
    expect(container.querySelector(".answer")?.textContent).not.toContain("[9]");
    expect(container.querySelector(".answer img")).toBeNull();
  });
});

describe("grouped citations", () => {
  beforeEach(() => { cleanup(); vi.clearAllMocks(); vi.mocked(api.studentMaterials).mockResolvedValue([]); });

  it("renders [1, 2] as separate citations and drops unknown numbers", async () => {
    vi.mocked(api.studentMessages).mockResolvedValue([{
      message_id: 4, question: "Q", answer: "Too large diverges [1, 2, 7].",
      sources: [{ n: 1, material: "a.pdf", section: "p. 1" }, { n: 2, material: "b.md", section: "text" }],
    }]);
    const { container } = render(<Student />);
    expect(await screen.findByText(/Too large diverges/)).toBeInTheDocument();
    expect(Array.from(container.querySelectorAll(".answer sup")).map(s => s.textContent)).toEqual(["[1]", "[2]"]);
    expect(container.querySelector(".answer")?.textContent).not.toContain("7");
  });
});
