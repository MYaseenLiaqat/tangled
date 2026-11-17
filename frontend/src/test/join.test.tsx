import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import App from "../App";

afterEach(() => cleanup());

describe("student entry", () => {
  it("links students from the login page to the join page", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: /join your course with a code/i })).toHaveAttribute("href", "/join");
  });

  it("lets a student type a code when they have no join link", () => {
    render(<MemoryRouter initialEntries={["/join"]}><App /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: "Join course" })).toBeInTheDocument();
    expect(screen.getByLabelText("Course code")).toHaveValue("");
  });
});
