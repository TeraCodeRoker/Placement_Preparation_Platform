import { getJSON, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

// Start returns { session_id, message, question: {...} }; flatten the question
// so callers get the question fields alongside the session id.
export async function startInterview(
  { difficulty = "medium", numSubjective = 5, numDsa = 2 } = {},
  opts
) {
  const res = await postJSON(
    ENDPOINTS.interview.start,
    { difficulty, num_subjective: numSubjective, num_dsa: numDsa },
    opts
  );
  return { session_id: res.session_id, ...res.question };
}

// Sends an idempotency key so a retried submit can't double-count the score.
export function submitAnswer({ sessionId, answer, idempotencyKey }, opts) {
  return postJSON(
    ENDPOINTS.interview.answer,
    { session_id: sessionId, answer, idempotency_key: idempotencyKey ?? crypto.randomUUID() },
    opts
  );
}

export function reviewCode({ question, userCode, language }, opts) {
  return postJSON(ENDPOINTS.interview.codeReview, { question, user_code: userCode, language }, opts);
}

export function interviewHistory({ limit = 20, offset = 0 } = {}, opts) {
  return getJSON(`${ENDPOINTS.interview.history}?limit=${limit}&offset=${offset}`, opts);
}
