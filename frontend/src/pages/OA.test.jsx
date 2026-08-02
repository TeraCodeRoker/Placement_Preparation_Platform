import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import OA from "./OA";

const mockOa = vi.hoisted(() => ({
  generateProblem: vi.fn(),
  runCode: vi.fn(),
  submitCode: vi.fn(),
}));
vi.mock("../api/oa", () => mockOa);
vi.mock("../api/auth", () => ({
  restore: vi.fn().mockResolvedValue(null),
  ensureGuest: vi.fn().mockResolvedValue("guest-token"),
}));
// Stub the lazy Monaco editor so tests don't load the heavy dependency.
vi.mock("../components/CodeEditor", () => ({
  default: ({ value, onChange }) => (
    <textarea aria-label="code editor" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

const PROBLEM = {
  problem_id: "p1",
  title: "Two Sum",
  statement: "Add two numbers",
  starter_code: { python: "# solve" },
  visible_tests: [{ stdin: "a", expected_output: "1" }],
  time_complexity_hint: "O(n)",
};

beforeEach(() => {
  vi.clearAllMocks();
  mockOa.generateProblem.mockResolvedValue(PROBLEM);
});

function renderOA() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <OA />
      </MemoryRouter>
    </AuthProvider>
  );
}

it("generates a problem and grades a submission with separate signals", async () => {
  mockOa.submitCode.mockResolvedValue({
    submission_id: "s1",
    test_results: [
      { index: 0, visible: true, passed: true, expected_output: "1" },
      { index: 1, visible: false, passed: false },
    ],
    pass_count: 1,
    total_count: 2,
    final_score: 50,
    mode: "graded",
    ai_review: { review_score: 7, correctness_rationale: "ok", time_complexity: "O(n)", suggestions: [] },
  });
  const user = userEvent.setup();
  renderOA();

  await user.click(screen.getByRole("button", { name: /generate problem/i }));
  await waitFor(() => expect(screen.getByText("Two Sum")).toBeInTheDocument());

  await user.click(screen.getByRole("button", { name: /submit/i }));
  await waitFor(() =>
    expect(screen.getByText("1/2 test cases passed")).toBeInTheDocument()
  );
  // Objective pass-rate and subjective AI score shown separately, not conflated.
  expect(screen.getByText(/AI review: 7\/10/)).toBeInTheDocument();
});

it("shows a degraded banner when execution was unavailable", async () => {
  mockOa.submitCode.mockResolvedValue({
    submission_id: "s2",
    test_results: [],
    pass_count: 0,
    total_count: 2,
    final_score: 0,
    mode: "ai_review_only",
    ai_review: { review_score: 6, correctness_rationale: "review", time_complexity: "O(n)", suggestions: [] },
  });
  const user = userEvent.setup();
  renderOA();

  await user.click(screen.getByRole("button", { name: /generate problem/i }));
  await waitFor(() => expect(screen.getByText("Two Sum")).toBeInTheDocument());
  await user.click(screen.getByRole("button", { name: /submit/i }));

  await waitFor(() =>
    expect(screen.getByText(/Objective execution was unavailable/i)).toBeInTheDocument()
  );
});
