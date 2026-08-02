import { getJSON, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

// Returns { set_id, topic, subtopic, difficulty, count, questions: [...] }.
export function generateMcqs({ topic, subtopic = "", count = 5, difficulty = "medium" }, opts) {
  return postJSON(ENDPOINTS.mcq.generate, { topic, subtopic, count, difficulty }, opts);
}

export function dailyChallenge({ topic = "mixed" } = {}, opts) {
  return postJSON(ENDPOINTS.mcq.dailyChallenge, { topic }, opts);
}

export function recordAttempt({ setId, subject = "", difficulty = "", correct, total }, opts) {
  return postJSON(
    ENDPOINTS.mcq.attempt,
    { set_id: setId ?? null, subject, difficulty, correct, total },
    opts
  );
}

export function mcqHistory({ limit = 20, offset = 0 } = {}, opts) {
  return getJSON(`${ENDPOINTS.mcq.history}?limit=${limit}&offset=${offset}`, opts);
}
