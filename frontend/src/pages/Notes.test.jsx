import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import Notes from "./Notes";

const mockNotes = vi.hoisted(() => ({ listNotes: vi.fn() }));
vi.mock("../api/notes", () => mockNotes);
vi.mock("../api/auth", () => ({ restore: vi.fn().mockResolvedValue(null) }));

beforeEach(() => vi.clearAllMocks());

function renderNotes() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <Notes />
      </MemoryRouter>
    </AuthProvider>
  );
}

it("fetches and groups published notes by subject", async () => {
  mockNotes.listNotes.mockResolvedValue([
    { id: "1", title: "Scheduling", subject: "Operating Systems", content_or_url: "text", approved: true, created_at: "2026-07-01" },
    { id: "2", title: "Normalization", subject: "DBMS", content_or_url: "https://ex.com", approved: true, created_at: "2026-07-01" },
  ]);
  renderNotes();
  await waitFor(() => expect(screen.getByText("Scheduling")).toBeInTheDocument());
  expect(screen.getByText("Operating Systems")).toBeInTheDocument();
  expect(screen.getByText("DBMS")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Open resource" })).toHaveAttribute("href", "https://ex.com");
});

it("shows an empty state when there are no notes", async () => {
  mockNotes.listNotes.mockResolvedValue([]);
  renderNotes();
  await waitFor(() =>
    expect(screen.getByText(/No notes have been published yet/i)).toBeInTheDocument()
  );
});
