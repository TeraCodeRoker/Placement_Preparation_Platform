import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import AdminNotes from "./AdminNotes";

const mockNotes = vi.hoisted(() => ({
  adminListNotes: vi.fn(),
  createNote: vi.fn(),
  updateNote: vi.fn(),
}));
const mockAuth = vi.hoisted(() => ({ restore: vi.fn() }));
vi.mock("../api/notes", () => mockNotes);
vi.mock("../api/auth", () => mockAuth);

beforeEach(() => {
  vi.clearAllMocks();
  mockNotes.adminListNotes.mockResolvedValue([]);
});

function renderAdmin() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <AdminNotes />
      </MemoryRouter>
    </AuthProvider>
  );
}

it("blocks non-admin users", async () => {
  mockAuth.restore.mockResolvedValue({ email: "u@x.com", role: "user", id: "1" });
  renderAdmin();
  await waitFor(() => expect(screen.getByText("Admins only")).toBeInTheDocument());
});

it("lets an admin publish a note", async () => {
  mockAuth.restore.mockResolvedValue({ email: "a@x.com", role: "admin", id: "1" });
  mockNotes.createNote.mockResolvedValue({ id: "n1" });
  const user = userEvent.setup();
  renderAdmin();

  await waitFor(() => expect(screen.getByText("Manage notes")).toBeInTheDocument());
  await user.type(screen.getByLabelText("Title"), "OS Cheatsheet");
  await user.type(screen.getByLabelText("Subject"), "Operating Systems");
  await user.type(screen.getByLabelText("Content or URL"), "https://ex.com/os");
  await user.click(screen.getByRole("button", { name: /publish note/i }));

  await waitFor(() =>
    expect(mockNotes.createNote).toHaveBeenCalledWith({
      title: "OS Cheatsheet",
      subject: "Operating Systems",
      contentOrUrl: "https://ex.com/os",
      approved: true,
    })
  );
});
