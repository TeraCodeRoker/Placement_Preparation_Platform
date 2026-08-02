import { postForm, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

// POST /ai/resume/analyze-pdf (multipart) -> { resume_text, target_role, analysis }
export function analyzePdf({ file, targetRole, targetCompanies = "" }, opts) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("target_role", targetRole);
  fd.append("target_companies", targetCompanies);
  return postForm(ENDPOINTS.resume.analyzePdf, fd, opts);
}

// POST /ai/resume/analyze (JSON) -> ResumeAnalysis
export function analyzeResume({ resumeText, targetRole, targetCompanies = [] }, opts) {
  return postJSON(
    ENDPOINTS.resume.analyze,
    { resume_text: resumeText, target_role: targetRole, target_companies: targetCompanies },
    opts
  );
}

// POST /ai/resume/ats-score (JSON) -> Ats result
export function atsScore({ resumeText, jobDescription }, opts) {
  return postJSON(
    ENDPOINTS.resume.atsScore,
    { resume_text: resumeText, job_description: jobDescription },
    opts
  );
}

// POST /ai/resume/pdf-to-json (multipart) -> { filename, resume_text, structured }
export function pdfToJson({ file }, opts) {
  const fd = new FormData();
  fd.append("file", file);
  return postForm(ENDPOINTS.resume.pdfToJson, fd, opts);
}
