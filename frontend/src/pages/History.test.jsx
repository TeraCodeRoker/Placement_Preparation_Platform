import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import History from "./History";

const mockInterview = vi.hoisted(() => ({ interviewHistory: vi.fn() }));
const mockMcq = vi.hoisted(() => ({ mcqHistory: vi.fn() }));
const mockAuth = vi.hoisted(() => ({ restore: vi.fn() }));
vi.mock("../api/interview", () => mockInterview);
vi.mock("../api/mcq", () => mockMcq);
vi.mock("../api/auth", () => mockAuth);

beforeEach(() => vi.clearAllMocks());

function renderHistory() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <History />
      </MemoryRouter>
    </AuthProvider>
  );
}

it("shows server-synced history for a logged-in user", async () => {
  mockAuth.restore.mockResolvedValue({ email: "a@x.com", role: "user", id: "1" });
  mockInterview.interviewHistory.mockResolvedValue([
    { session_id: "s1", status: "complete", total_questions: 7, created_at: "2026-07-01T10:00:00Z" },
  ]);
  mockMcq.mcqHistory.mockResolvedValue([{ id: "m1", subject: "OS", correct: 4, total: 5, percent: 80 }]);

  renderHistory();
  await waitFor(() => expect(screen.getByText("Synced to your account.")).toBeInTheDocument());
  expect(screen.getByText("7 questions")).toBeInTheDocument();
  expect(screen.getByText(/4\/5 · 80%/)).toBeInTheDocument();
});

it("shows a guest prompt when not logged in", async () => {
  mockAuth.restore.mockResolvedValue(null);
  renderHistory();
  await waitFor(() =>
    expect(screen.getByText(/browsing as a guest/i)).toBeInTheDocument()
  );
});
