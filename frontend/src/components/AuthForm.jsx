import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Alert, Eyebrow, Spinner } from "./ui";

// Shared, accessible login/register form (labeled inputs, keyboard-operable).
export default function AuthForm({ mode }) {
  const isRegister = mode === "register";
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await (isRegister ? register({ email, password }) : login({ email, password }));
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md animate-fade-up">
      <Eyebrow>{isRegister ? "create account" : "welcome back"}</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">
        {isRegister ? "Sign up" : "Log in"}
      </h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        {isRegister
          ? "Save your history across sessions. Everything still works as a guest without an account."
          : "Log in to see your saved interview, MCQ, and OA history."}
      </p>

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      <form className="card mt-6 space-y-5 p-6" onSubmit={onSubmit} noValidate>
        <div>
          <label className="field-label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="field"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            required
            minLength={8}
            className="field"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {isRegister && <p className="mt-1 text-xs text-gray-500">At least 8 characters.</p>}
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading && <Spinner />}
          {isRegister ? "Create account" : "Log in"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        {isRegister ? (
          <>
            Already have an account?{" "}
            <Link className="font-medium text-brand-600 hover:underline dark:text-brand-400" to="/login">
              Log in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link
              className="font-medium text-brand-600 hover:underline dark:text-brand-400"
              to="/register"
            >
              Create an account
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
