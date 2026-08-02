import { getJSON, patchJSON, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

export function listNotes(opts) {
  return getJSON(ENDPOINTS.notes.list, opts);
}

export function adminListNotes(opts) {
  return getJSON(ENDPOINTS.notes.adminList, opts);
}

export function createNote({ title, subject = "", contentOrUrl, approved = false }, opts) {
  return postJSON(
    ENDPOINTS.notes.adminCreate,
    { title, subject, content_or_url: contentOrUrl, approved },
    opts
  );
}

export function updateNote(id, data, opts) {
  return patchJSON(ENDPOINTS.notes.adminUpdate(id), data, opts);
}
