import { lazy, Suspense } from "react";
import { Spinner } from "./ui";

// Monaco is a heavy dependency, so it's lazy-loaded (its own chunk) and never in
// the main bundle — this keeps first paint fast, which matters against a
// cold-starting free backend (perf budget, §9.5).
const MonacoEditor = lazy(() => import("@monaco-editor/react"));

export default function CodeEditor({ language, value, onChange, height = "360px" }) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-night-600">
      <Suspense
        fallback={
          <div className="grid place-items-center bg-gray-50 dark:bg-night-800" style={{ height }}>
            <Spinner />
          </div>
        }
      >
        <MonacoEditor
          height={height}
          language={language === "cpp" ? "cpp" : language}
          value={value}
          onChange={(v) => onChange(v ?? "")}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </Suspense>
    </div>
  );
}
