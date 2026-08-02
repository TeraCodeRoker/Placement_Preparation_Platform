import { Link } from "react-router-dom";
import { Eyebrow } from "../components/ui";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg py-20 text-center animate-fade-up">
      <Eyebrow>404</Eyebrow>
      <h1 className="mt-3 font-display text-4xl font-bold">Page not found</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        That route doesn’t exist. Let’s get you back to your prep.
      </p>
      <Link to="/" className="btn-primary mt-6">
        Back to home
      </Link>
    </div>
  );
}
