import { getJSON, patchJSON, postJSON } from "./client";
import { ENDPOINTS } from "./endpoints";

const PAGE_SIZE = 100; // the API's max_limit

export function listNotes(opts) {
  return getJSON(ENDPOINTS.notes.list, opts);
}

/**
 * Fetch the whole notes library.
 *
 * The endpoint is capped at 100 rows per request (a deliberate server guardrail),
 * and the library is already ~100 notes. Paging is an artifact of that transport
 * limit, not something the Notes page should reason about — so it stops here.
 */
export async function listAllNotes({ signal } = {}) {
  const all = [];
  for (let offset = 0; ; offset += PAGE_SIZE) {
    const page = await getJSON(`${ENDPOINTS.notes.list}?limit=${PAGE_SIZE}&offset=${offset}`, {
      signal,
    });
    if (!Array.isArray(page) || page.length === 0) break;
    all.push(...page);
    if (page.length < PAGE_SIZE) break; // short page = last page
  }
  return all;
}

export function adminListNotes(opts) {
  return getJSON(ENDPOINTS.notes.adminList, opts);
}

export function createNote(
  { title, subject = "", unit = "", kind = "link", contentOrUrl, approved = false },
  opts
) {
  return postJSON(
    ENDPOINTS.notes.adminCreate,
    { title, subject, unit, kind, content_or_url: contentOrUrl, approved },
    opts
  );
}

export function updateNote(id, data, opts) {
  return patchJSON(ENDPOINTS.notes.adminUpdate(id), data, opts);
}
