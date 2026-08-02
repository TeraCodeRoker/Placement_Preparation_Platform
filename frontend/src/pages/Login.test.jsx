import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import Login from "./Login";

const mockAuth = vi.hoisted(() => ({
  restore: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}));
vi.mock("../api/auth", () => mockAuth);

beforeEach(() => {
  vi.clearAllMocks();
  mockAuth.restore.mockResolvedValue(null);
});

function renderLogin() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>HOME PAGE</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

it("logs in with labeled inputs and navigates home", async () => {
  mockAuth.login.mockResolvedValue({ email: "a@b.com", role: "user", id: "1" });
  const user = userEvent.setup();
  renderLogin();

  await user.type(screen.getByLabelText("Email"), "a@b.com");
  await user.type(screen.getByLabelText("Password"), "password123");
  await user.click(screen.getByRole("button", { name: "Log in" }));

  expect(mockAuth.login).toHaveBeenCalledWith({ email: "a@b.com", password: "password123" });
  await waitFor(() => expect(screen.getByText("HOME PAGE")).toBeInTheDocument());
});

it("shows an error when login fails", async () => {
  mockAuth.login.mockRejectedValue(new Error("Invalid email or password."));
  const user = userEvent.setup();
  renderLogin();

  await user.type(screen.getByLabelText("Email"), "a@b.com");
  await user.type(screen.getByLabelText("Password"), "wrongpass");
  await user.click(screen.getByRole("button", { name: "Log in" }));

  await waitFor(() =>
    expect(screen.getByText("Invalid email or password.")).toBeInTheDocument()
  );
});
