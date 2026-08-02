import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AuthMenu() {
  const { user, status, logout } = useAuth();

  if (status === "authed" && user) {
    return (
      <div className="flex items-center gap-2">
        <span className="hidden max-w-[12rem] truncate text-sm text-gray-600 sm:inline dark:text-gray-300">
          {user.email}
        </span>
        <button className="btn-ghost !px-3 text-sm" onClick={logout}>
          Log out
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <Link to="/login" className="btn-ghost !px-3 text-sm">
        Log in
      </Link>
      <Link
        to="/register"
        className="hidden rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600 sm:inline-block"
      >
        Sign up
      </Link>
    </div>
  );
}
