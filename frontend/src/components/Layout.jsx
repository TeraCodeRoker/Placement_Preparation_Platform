import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import WakingServer from "./WakingServer";

function Footer() {
  return (
    <footer className="mt-20 border-t border-gray-200 dark:border-night-700">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-8 text-sm text-gray-500 sm:flex-row sm:px-6">
        <p className="font-display font-semibold">
          Prep<span className="text-brand-500">stack</span>
        </p>
        <p className="font-mono text-xs">Built for campus placement prep · {new Date().getFullYear()}</p>
      </div>
    </footer>
  );
}

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <WakingServer />
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
