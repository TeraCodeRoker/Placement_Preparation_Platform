// ---------------------------------------------------------------------------
// Single integration point for the backend.
// ---------------------------------------------------------------------------
// Every network call flows through here. Adds auth (in-memory access token,
// guest token, CSRF header), transparently refreshes a 401 once, and maps the
// backend's { error: { code, message } } envelope to a readable Error.
//
// Same-origin by default ("/api/v1"): in dev, vite proxies /api to the backend;
// in prod, a Render static-site rewrite proxies /api to the web service, so the
// httpOnly refresh cookie is same-site.
// ---------------------------------------------------------------------------

export const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export function url(path) {
  return `${API_BASE}${path}`;
}

// --- auth token state (access token in memory only; never localStorage) ---
let accessToken = null;
let guestToken = null;
const GUEST_KEY = "prepstack:guest";

export function setAccessToken(token) {
  accessToken = token;
}
export function getAccessToken() {
  return accessToken;
}
export function setGuestToken(token) {
  guestToken = token;
  try {
    if (token) localStorage.setItem(GUEST_KEY, token);
  } catch {
    /* private mode — guest token stays in memory only */
  }
}
export function getGuestToken() {
  if (guestToken) return guestToken;
  try {
    guestToken = localStorage.getItem(GUEST_KEY);
  } catch {
    /* ignore */
  }
  return guestToken;
}

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const guest = getGuestToken();
  if (guest) headers["X-Guest-Token"] = guest;
  const csrf = readCookie("prepstack_csrf");
  if (csrf) headers["X-CSRF-Token"] = csrf; // double-submit for cookie routes
  return headers;
}

async function toError(res) {
  let message = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (body?.error?.message) message = body.error.message;
    else if (body?.detail) message = typeof body.detail === "string" ? body.detail : message;
    else if (body?.message) message = body.message;
  } catch {
    /* non-JSON body — keep the status message */
  }
  const err = new Error(message);
  err.status = res.status;
  return err;
}

// De-duped single-flight refresh so parallel 401s trigger one refresh call.
let refreshInFlight = null;
async function tryRefresh() {
  if (!refreshInFlight) {
    refreshInFlight = fetch(url("/auth/refresh"), {
      method: "POST",
      headers: authHeaders(),
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) return false;
        const body = await res.json();
        setAccessToken(body.access_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        // Allow the next batch of 401s to refresh again later.
        setTimeout(() => {
          refreshInFlight = null;
        }, 0);
      });
  }
  return refreshInFlight;
}

async function request(path, options = {}, { retry = true } = {}) {
  const res = await fetch(url(path), {
    ...options,
    headers: authHeaders(options.headers),
    credentials: "include",
  });
  if (res.status === 401 && retry && path !== "/auth/refresh") {
    if (await tryRefresh()) return request(path, options, { retry: false });
  }
  if (!res.ok) throw await toError(res);
  if (res.status === 204) return null;
  return res.json();
}

export function postJSON(path, data, { signal } = {}) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data ?? {}),
    signal,
  });
}

export function getJSON(path, { signal } = {}) {
  return request(path, { method: "GET", signal });
}

export function patchJSON(path, data, { signal } = {}) {
  return request(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data ?? {}),
    signal,
  });
}

export function postForm(path, formData, { signal } = {}) {
  return request(path, { method: "POST", body: formData, signal });
}
