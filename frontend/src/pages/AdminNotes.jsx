import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminListNotes, createNote, updateNote } from "../api/notes";
import { Alert, Eyebrow, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function AdminNotes() {
  const { user, status } = useAuth();
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [contentOrUrl, setContentOrUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isAdmin = status === "authed" && user?.role === "admin";

  async function refresh() {
    try {
      setNotes(await adminListNotes());
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (isAdmin) refresh();
  }, [isAdmin]);

  if (status === "loading") {
    return (
      <div className="grid place-items-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-md animate-fade-up text-center">
        <h1 className="font-display text-2xl font-bold">Admins only</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          You need an administrator account to manage notes.
        </p>
        <Link className="mt-4 inline-block font-medium text-brand-600 dark:text-brand-400" to="/notes">
          Back to notes
        </Link>
      </div>
    );
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await createNote({ title, subject, contentOrUrl, approved: true });
      setTitle("");
      setSubject("");
      setContentOrUrl("");
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function toggleApproved(note) {
    try {
      await updateNote(note.id, { approved: !note.approved });
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <Eyebrow>admin</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">Manage notes</h1>

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      <form className="card mt-6 space-y-4 p-6" onSubmit={handleCreate}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="note-title">
              Title
            </label>
            <input
              id="note-title"
              className="field"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="field-label" htmlFor="note-subject">
              Subject
            </label>
            <input
              id="note-subject"
              className="field"
              placeholder="e.g. Operating Systems"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="field-label" htmlFor="note-content">
            Content or URL
          </label>
          <input
            id="note-content"
            className="field"
            required
            placeholder="https://… or a short note"
            value={contentOrUrl}
            onChange={(e) => setContentOrUrl(e.target.value)}
          />
        </div>
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading && <Spinner />}
          Publish note
        </button>
      </form>

      <div className="card mt-6 p-6">
        <p className="eyebrow">all notes</p>
        <ul className="mt-3 divide-y divide-gray-100 dark:divide-night-700">
          {notes.map((note) => (
            <li key={note.id} className="flex items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{note.title}</p>
                <p className="truncate text-xs text-gray-500">{note.subject || "General"}</p>
              </div>
              <button
                className={`chip ${
                  note.approved
                    ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
                    : "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
                }`}
                onClick={() => toggleApproved(note)}
              >
                {note.approved ? "approved" : "pending"}
              </button>
            </li>
          ))}
          {notes.length === 0 && <li className="py-3 text-sm text-gray-500">No notes yet.</li>}
        </ul>
      </div>
    </div>
  );
}
