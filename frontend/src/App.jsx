import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import AdminNotes from "./pages/AdminNotes";
import History from "./pages/History";
import Home from "./pages/Home";
import Login from "./pages/Login";
import McqPractice from "./pages/McqPractice";
import MockInterview from "./pages/MockInterview";
import NotFound from "./pages/NotFound";
import Notes from "./pages/Notes";
import Register from "./pages/Register";
import ResumeChecker from "./pages/ResumeChecker";
import Sheets from "./pages/Sheets";

// OA pulls in Monaco (lazy) — code-split so it never bloats the main bundle.
const OA = lazy(() => import("./pages/OA"));

function RouteFallback() {
  return (
    <div className="grid place-items-center py-24">
      <Spinner className="h-8 w-8" />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="/interview" element={<MockInterview />} />
        <Route path="/resume" element={<ResumeChecker />} />
        <Route path="/mcq" element={<McqPractice />} />
        <Route
          path="/oa"
          element={
            <Suspense fallback={<RouteFallback />}>
              <OA />
            </Suspense>
          }
        />
        <Route path="/notes" element={<Notes />} />
        <Route path="/notes/admin" element={<AdminNotes />} />
        <Route path="/history" element={<History />} />
        <Route path="/sheets" element={<Sheets />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
