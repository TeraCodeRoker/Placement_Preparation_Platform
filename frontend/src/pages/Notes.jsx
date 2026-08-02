import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listNotes } from "../api/notes";
import { Alert, Eyebrow, Spinner } from "../components/ui";
import { IconBook, IconDoc } from "../components/icons";
import { useAuth } from "../context/AuthContext";

function isUrl(value) {
  return /^https?:\/\//i.test(value);
}

function groupBySubject(notes) {
  const groups = new Map();
  for (const note of notes) {
    const key = note.subject || "General";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(note);
  }
  return [...groups.entries()];
}

export default function Notes() {
  const { user } = useAuth();
  const [notes, setNotes] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    listNotes()
      .then((data) => active && setNotes(data))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow>subject notes</Eyebrow>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">Notes Library</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Study notes published by admins, grouped by subject.
          </p>
        </div>
        {user?.role === "admin" && (
          <Link
            to="/notes/admin"
            className="shrink-0 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
          >
            Admin panel
          </Link>
        )}
      </div>

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {notes === null && !error && (
        <div className="mt-10 grid place-items-center">
          <Spinner className="h-8 w-8" />
        </div>
      )}

      {notes && notes.length === 0 && (
        <div className="mt-6">
          <Alert tone="info">No notes have been published yet — check back soon.</Alert>
        </div>
      )}

      {notes && notes.length > 0 && (
        <div className="mt-6 space-y-5">
          {groupBySubject(notes).map(([subject, items]) => (
            <div key={subject} className="card p-6">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                  <IconBook className="h-5 w-5" />
                </span>
                <h2 className="font-display text-xl font-semibold">{subject}</h2>
              </div>
              <ul className="mt-4 divide-y divide-gray-100 dark:divide-night-700">
                {items.map((note) => (
                  <li key={note.id} className="flex items-center gap-3 py-3">
                    <IconDoc className="h-4 w-4 shrink-0 text-gray-400" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{note.title}</p>
                      {isUrl(note.content_or_url) ? (
                        <a
                          href={note.content_or_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-brand-600 hover:underline dark:text-brand-400"
                        >
                          Open resource
                        </a>
                      ) : (
                        <p className="truncate text-xs text-gray-500">{note.content_or_url}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
