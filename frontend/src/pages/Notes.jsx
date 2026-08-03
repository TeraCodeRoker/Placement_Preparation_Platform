import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listAllNotes } from "../api/notes";
import { Alert, Eyebrow, Spinner } from "../components/ui";
import { IconBook, IconDoc, IconExternal, IconList } from "../components/icons";
import { useAuth } from "../context/AuthContext";

function isUrl(value) {
  return /^https?:\/\//i.test(value);
}

/** A file the browser can fetch (static asset or absolute URL) vs inline text. */
function isResource(note) {
  return isUrl(note.content_or_url) || note.content_or_url.startsWith("/");
}

function formatSize(bytes) {
  if (!bytes) return "";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const KIND_LABEL = {
  pdf: "PDF",
  slides: "Slides",
  doc: "Document",
  syllabus: "Syllabus",
  image: "Image",
  link: "Link",
  text: "Note",
};

/**
 * Shape the flat API list into subject -> unit -> items.
 *
 * The server returns one flat, ordered collection; the hierarchy is a *view*
 * concern, so it is built here rather than baked into the endpoint. That keeps
 * the API a single cacheable resource while the UI stays free to regroup.
 */
function buildLibrary(notes) {
  const subjects = new Map();
  for (const note of notes) {
    const subjectKey = note.subject || "General";
    if (!subjects.has(subjectKey)) subjects.set(subjectKey, new Map());
    const units = subjects.get(subjectKey);
    const unitKey = note.unit || "Other";
    if (!units.has(unitKey)) units.set(unitKey, []);
    units.get(unitKey).push(note);
  }
  return [...subjects.entries()].map(([subject, units]) => ({
    subject,
    count: [...units.values()].reduce((n, items) => n + items.length, 0),
    units: [...units.entries()].map(([unit, items]) => ({ unit, items })),
  }));
}

function matches(note, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  return (
    note.title.toLowerCase().includes(q) ||
    (note.subject || "").toLowerCase().includes(q) ||
    (note.unit || "").toLowerCase().includes(q)
  );
}

function NoteRow({ note }) {
  const size = formatSize(note.size_bytes);
  const kind = KIND_LABEL[note.kind] || "File";
  const external = isUrl(note.content_or_url);

  if (!isResource(note)) {
    return (
      <li className="py-3">
        <p className="text-sm font-medium">{note.title}</p>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{note.content_or_url}</p>
      </li>
    );
  }

  return (
    <li className="py-1">
      <a
        href={note.content_or_url}
        target="_blank"
        rel="noreferrer"
        // The visible text is just the title, so spell out type and weight for
        // screen readers — and for anyone deciding whether to spend the data.
        aria-label={`${note.title} — ${kind}${size ? `, ${size}` : ""}`}
        className="group flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:hover:bg-night-800"
      >
        <IconDoc className="h-4 w-4 shrink-0 text-gray-400 group-hover:text-brand-500" />
        <span className="min-w-0 flex-1 truncate text-sm font-medium">{note.title}</span>
        <span className="shrink-0 rounded-md bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600 dark:bg-night-700 dark:text-gray-300">
          {kind}
        </span>
        {size && (
          <span className="shrink-0 text-xs tabular-nums text-gray-400" aria-hidden="true">
            {size}
          </span>
        )}
        {external && <IconExternal className="h-3.5 w-3.5 shrink-0 text-gray-400" />}
      </a>
    </li>
  );
}

function UnitSection({ subjectId, unit, items, open, onToggle }) {
  const panelId = `${subjectId}-${unit.replace(/\s+/g, "-")}`;
  return (
    <div className="border-t border-gray-100 first:border-t-0 dark:border-night-700">
      <h3>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={panelId}
          className="flex w-full items-center gap-3 py-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <span
            className={`text-gray-400 transition-transform ${open ? "rotate-90" : ""}`}
            aria-hidden="true"
          >
            ▶
          </span>
          <span className="flex-1 text-sm font-semibold">{unit}</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {items.length} {items.length === 1 ? "file" : "files"}
          </span>
        </button>
      </h3>
      {open && (
        <ul id={panelId} className="pb-3 pl-6">
          {items.map((note) => (
            <NoteRow key={note.id} note={note} />
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Notes() {
  const { user } = useAuth();
  const [notes, setNotes] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [openUnits, setOpenUnits] = useState(() => new Set());

  useEffect(() => {
    const controller = new AbortController();
    listAllNotes({ signal: controller.signal })
      .then(setNotes)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, []);

  const library = useMemo(() => {
    if (!notes) return [];
    return buildLibrary(notes.filter((n) => matches(n, query)));
  }, [notes, query]);

  // While searching, reveal every match — hiding hits inside collapsed units
  // would make the search look broken.
  const searching = query.trim().length > 0;
  const toggle = (key) =>
    setOpenUnits((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  const totalShown = library.reduce((n, s) => n + s.count, 0);

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow>subject notes</Eyebrow>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">Notes Library</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Curated study material, organised by subject and unit.
          </p>
        </div>
        {user?.role === "admin" && (
          <Link
            to="/notes/admin"
            className="shrink-0 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            Admin panel
          </Link>
        )}
      </div>

      {notes && notes.length > 0 && (
        <div className="mt-6">
          <label htmlFor="notes-search" className="sr-only">
            Search notes by title, subject or unit
          </label>
          <input
            id="notes-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search notes…"
            className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-night-700 dark:bg-night-800"
          />
          <p className="sr-only" role="status" aria-live="polite">
            {totalShown} {totalShown === 1 ? "note" : "notes"} shown
          </p>
        </div>
      )}

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {notes === null && !error && (
        <div className="mt-10 grid place-items-center">
          <Spinner className="h-8 w-8" />
          <p className="sr-only" role="status">
            Loading notes
          </p>
        </div>
      )}

      {notes && notes.length === 0 && (
        <div className="mt-6">
          <Alert tone="info">No notes have been published yet — check back soon.</Alert>
        </div>
      )}

      {notes && notes.length > 0 && library.length === 0 && (
        <div className="mt-6">
          <Alert tone="info">No notes match “{query}”.</Alert>
        </div>
      )}

      <div className="mt-6 space-y-5">
        {library.map(({ subject, units, count }) => (
          <section key={subject} className="card p-6" aria-labelledby={`subject-${subject}`}>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                <IconBook className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h2
                  id={`subject-${subject}`}
                  className="font-display text-xl font-semibold"
                >
                  {subject}
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  <IconList className="mr-1 inline h-3 w-3" aria-hidden="true" />
                  {count} {count === 1 ? "file" : "files"} · {units.length}{" "}
                  {units.length === 1 ? "unit" : "units"}
                </p>
              </div>
            </div>
            <div className="mt-3">
              {units.map(({ unit, items }) => {
                const key = `${subject}::${unit}`;
                return (
                  <UnitSection
                    key={key}
                    subjectId={subject.replace(/\s+/g, "-")}
                    unit={unit}
                    items={items}
                    open={searching || openUnits.has(key)}
                    onToggle={() => toggle(key)}
                  />
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
