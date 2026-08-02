import { getJSON, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

export function generateProblem({ step, topic, languages = ["python"], numHidden = 5 }, opts) {
  return postJSON(
    ENDPOINTS.oa.problem,
    { step, topic, languages, num_hidden: numHidden },
    opts
  );
}

export function runCode({ problemId, language, sourceCode }, opts) {
  return postJSON(
    ENDPOINTS.oa.run,
    { problem_id: problemId, language, source_code: sourceCode },
    opts
  );
}

export function submitCode({ problemId, language, sourceCode }, opts) {
  return postJSON(
    ENDPOINTS.oa.submit,
    { problem_id: problemId, language, source_code: sourceCode },
    opts
  );
}

export function getSubmission(id, opts) {
  return getJSON(ENDPOINTS.oa.submission(id), opts);
}
