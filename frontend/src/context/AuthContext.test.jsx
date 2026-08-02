import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";

const mockAuth = vi.hoisted(() => ({
  restore: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}));
vi.mock("../api/auth", () => mockAuth);

function Probe() {
  const { status, user } = useAuth();
  return <div data-testid="probe">{`${status}:${user?.email ?? ""}`}</div>;
}

beforeEach(() => {
  vi.clearAllMocks();
});

it("restores an authenticated session on mount", async () => {
  mockAuth.restore.mockResolvedValue({ email: "a@b.com", role: "user", id: "1" });
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
  await waitFor(() => expect(screen.getByTestId("probe")).toHaveTextContent("authed:a@b.com"));
});

it("falls back to guest when there is no session", async () => {
  mockAuth.restore.mockResolvedValue(null);
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
  await waitFor(() => expect(screen.getByTestId("probe")).toHaveTextContent("guest:"));
});
