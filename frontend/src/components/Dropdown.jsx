import { useEffect, useRef, useState } from "react";

/**
 * Accessible single-select dropdown.
 * options: [{ id, label, hint? }]
 */
export default function Dropdown({ options, value, onChange, label, className = "" }) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(() => Math.max(0, options.findIndex((o) => o.id === value)));
  const wrapRef = useRef(null);
  const listRef = useRef(null);

  const selected = options.find((o) => o.id === value) || options[0];

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  function pick(id) {
    onChange(id);
    setOpen(false);
  }

  function onKeyDown(e) {
    if (!open && (e.key === "Enter" || e.key === " " || e.key === "ArrowDown")) {
      e.preventDefault();
      setOpen(true);
      setActive(Math.max(0, options.findIndex((o) => o.id === value)));
      return;
    }
    if (!open) return;
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % options.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + options.length) % options.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(options[active].id);
    }
  }

  return (
    <div className={`relative ${className}`} ref={wrapRef}>
      {label && <span className="field-label">{label}</span>}
      <button
        type="button"
        className="field flex w-full items-center justify-between gap-3 text-left"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKeyDown}
      >
        <span className="min-w-0">
          <span className="block truncate font-medium">{selected?.label}</span>
          {selected?.hint && <span className="block truncate text-xs text-gray-500">{selected.hint}</span>}
        </span>
        <svg
          viewBox="0 0 24 24"
          className={`h-4 w-4 shrink-0 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <ul
          ref={listRef}
          role="listbox"
          tabIndex={-1}
          className="absolute z-30 mt-2 max-h-72 w-full overflow-auto rounded-xl border border-gray-200 bg-white p-1.5 shadow-lg dark:border-night-600 dark:bg-night-800"
          onKeyDown={onKeyDown}
        >
          {options.map((o, i) => {
            const isSel = o.id === value;
            return (
              <li key={o.id} role="option" aria-selected={isSel}>
                <button
                  type="button"
                  onMouseEnter={() => setActive(i)}
                  onClick={() => pick(o.id)}
                  className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                    i === active ? "bg-gray-100 dark:bg-night-700" : ""
                  } ${isSel ? "text-brand-700 dark:text-brand-300" : ""}`}
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium">{o.label}</span>
                    {o.hint && <span className="block truncate text-xs text-gray-500">{o.hint}</span>}
                  </span>
                  {isSel && (
                    <svg
                      viewBox="0 0 24 24"
                      className="h-4 w-4 shrink-0"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden
                    >
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
