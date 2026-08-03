import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import Notes from "./Notes";

const mockNotes = vi.hoisted(() => ({ listNotes: vi.fn(), listAllNotes: vi.fn() }));
vi.mock("../api/notes", () => mockNotes);
vi.mock("../api/auth", () => ({ restore: vi.fn().mockResolvedValue(null) }));

beforeEach(() => vi.clearAllMocks());

const note = (over) => ({
  id: "1",
  title: "Scheduling",
  subject: "Operating Systems",
  unit: "Unit 1",
  kind: "pdf",
  size_bytes: 1048576,
  content_or_url: "/notes/operating-systems/unit-1/scheduling.pdf",
  approved: true,
  created_at: "2026-07-01",
  ...over,
});

function renderNotes() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <Notes />
      </MemoryRouter>
    </AuthProvider>
  );
}

it("groups notes by subject and unit", async () => {
  mockNotes.listAllNotes.mockResolvedValue([
    note(),
    note({ id: "2", title: "Deadlocks", unit: "Unit 2" }),
    note({ id: "3", title: "Normalization", subject: "DBMS", unit: "Unit 1" }),
  ]);
  renderNotes();

  await waitFor(() =>
    expect(screen.getByRole("heading", { name: "Operating Systems" })).toBeInTheDocument()
  );
  expect(screen.getByRole("heading", { name: "DBMS" })).toBeInTheDocument();
  // Two units under OS, one under DBMS.
  expect(screen.getByRole("button", { name: /Unit 2/ })).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: /Unit 1/ })).toHaveLength(2);
});

it("keeps units collapsed until opened, exposing state to assistive tech", async () => {
  mockNotes.listAllNotes.mockResolvedValue([note()]);
  renderNotes();

  const toggle = await screen.findByRole("button", { name: /Unit 1/ });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  expect(screen.queryByRole("link", { name: /Scheduling/ })).not.toBeInTheDocument();

  await userEvent.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("link", { name: /Scheduling/ })).toBeInTheDocument();
});

it("labels each file with its type and size for screen readers", async () => {
  mockNotes.listAllNotes.mockResolvedValue([note()]);
  renderNotes();

  await userEvent.click(await screen.findByRole("button", { name: /Unit 1/ }));
  const link = screen.getByRole("link", { name: "Scheduling — PDF, 1.0 MB" });
  expect(link).toHaveAttribute("href", "/notes/operating-systems/unit-1/scheduling.pdf");
});

it("search filters notes and auto-expands matches", async () => {
  mockNotes.listAllNotes.mockResolvedValue([
    note(),
    note({ id: "2", title: "Normalization", subject: "DBMS", unit: "Unit 3" }),
  ]);
  renderNotes();
  await screen.findByRole("heading", { name: "Operating Systems" });

  await userEvent.type(screen.getByLabelText(/Search notes/i), "normal");

  // Matching note is revealed without needing a click; the other subject is gone.
  await waitFor(() =>
    expect(screen.getByRole("link", { name: /Normalization/ })).toBeInTheDocument()
  );
  expect(screen.queryByRole("heading", { name: "Operating Systems" })).not.toBeInTheDocument();
});

it("tells the user when a search matches nothing", async () => {
  mockNotes.listAllNotes.mockResolvedValue([note()]);
  renderNotes();
  await screen.findByRole("heading", { name: "Operating Systems" });

  await userEvent.type(screen.getByLabelText(/Search notes/i), "zzzz");
  await waitFor(() => expect(screen.getByText(/No notes match/i)).toBeInTheDocument());
});

it("renders inline text notes without a link", async () => {
  mockNotes.listAllNotes.mockResolvedValue([
    note({ content_or_url: "Round robin is preemptive.", kind: "text", size_bytes: 0 }),
  ]);
  renderNotes();

  await userEvent.click(await screen.findByRole("button", { name: /Unit 1/ }));
  expect(screen.getByText("Round robin is preemptive.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /Scheduling/ })).not.toBeInTheDocument();
});

it("shows an empty state when there are no notes", async () => {
  mockNotes.listAllNotes.mockResolvedValue([]);
  renderNotes();
  await waitFor(() =>
    expect(screen.getByText(/No notes have been published yet/i)).toBeInTheDocument()
  );
});

it("surfaces a load failure", async () => {
  mockNotes.listAllNotes.mockRejectedValue(new Error("Network down"));
  renderNotes();
  await waitFor(() => expect(screen.getByText("Network down")).toBeInTheDocument());
});

it("groups notes missing a unit under a fallback heading", async () => {
  mockNotes.listAllNotes.mockResolvedValue([note({ unit: "" })]);
  renderNotes();
  const toggle = await screen.findByRole("button", { name: /Other/ });
  expect(within(toggle).getByText("Other")).toBeInTheDocument();
});
