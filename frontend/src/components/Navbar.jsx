import { useState } from "react";
import { NavLink, Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";
import { IconSun, IconMoon, IconMenu, IconX } from "./icons";
import AuthMenu from "./AuthMenu";

const LINKS = [
  { to: "/interview", label: "Mock Interview" },
  { to: "/oa", label: "OA Compiler" },
  { to: "/resume", label: "Resume Checker" },
  { to: "/mcq", label: "MCQ Practice" },
  { to: "/notes", label: "Notes" },
  { to: "/history", label: "History" },
  { to: "/sheets", label: "DSA Sheets" },
];

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      className="btn-ghost !px-2.5"
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? <IconSun className="h-5 w-5" /> : <IconMoon className="h-5 w-5" />}
    </button>
  );
}

function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 font-display text-lg font-bold text-white">
        P
      </span>
      <span className="font-display text-lg font-bold tracking-tight">
        Prep<span className="text-brand-500">stack</span>
      </span>
    </Link>
  );
}

const linkClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive
      ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200"
      : "text-gray-600 hover:bg-gray-100 hover:text-night-900 dark:text-gray-300 dark:hover:bg-night-700 dark:hover:text-white"
  }`;

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-gray-50/80 backdrop-blur dark:border-night-700 dark:bg-night-900/80">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Wordmark />

        <div className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <AuthMenu />
          <ThemeToggle />
          <button
            className="btn-ghost !px-2.5 lg:hidden"
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle menu"
            aria-expanded={open}
          >
            {open ? <IconX className="h-5 w-5" /> : <IconMenu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-gray-200 px-4 py-2 lg:hidden dark:border-night-700">
          <div className="flex flex-col gap-1">
            {LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} className={linkClass} onClick={() => setOpen(false)}>
                {l.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
