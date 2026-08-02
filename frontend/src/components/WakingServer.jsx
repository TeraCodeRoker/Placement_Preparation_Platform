import { useEffect, useState } from "react";

// Render free instances spin down after 15 min idle and cold-start on the next
// request. Probe /health once on load; if it's slow (or the first hit fails),
// show a friendly "waking up" banner so the ~30-60s cold start doesn't look broken.
export default function WakingServer() {
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let done = false;
    const slowTimer = setTimeout(() => {
      if (!done) setWaking(true);
    }, 1500);

    fetch("/health", { method: "GET" })
      .catch(() => {})
      .finally(() => {
        done = true;
        clearTimeout(slowTimer);
        setWaking(false);
      });

    return () => {
      done = true;
      clearTimeout(slowTimer);
    };
  }, []);

  if (!waking) return null;

  return (
    <div
      role="status"
      className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-center text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
    >
      Waking up the server — the free instance can take up to a minute after inactivity…
    </div>
  );
}
