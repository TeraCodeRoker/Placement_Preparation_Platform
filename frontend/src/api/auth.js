import {
  getGuestToken,
  getJSON,
  postJSON,
  setAccessToken,
  setGuestToken,
} from "./client";
import { ENDPOINTS } from "./endpoints";

/** Register, store the access token, and attach any guest activity. */
export async function register({ email, password }) {
  const res = await postJSON(ENDPOINTS.auth.register, { email, password });
  setAccessToken(res.access_token);
  await claimGuestActivity();
  return res.user;
}

/** Log in, store the access token, and attach any guest activity. */
export async function login({ email, password }) {
  const res = await postJSON(ENDPOINTS.auth.login, { email, password });
  setAccessToken(res.access_token);
  await claimGuestActivity();
  return res.user;
}

export async function logout() {
  try {
    await postJSON(ENDPOINTS.auth.logout, {});
  } finally {
    setAccessToken(null);
  }
}

/** Silent session restore on load (access token is memory-only, lost on reload). */
export async function restore() {
  try {
    const res = await postJSON(ENDPOINTS.auth.refresh, {});
    setAccessToken(res.access_token);
    return res.user;
  } catch {
    return null;
  }
}

/** Ensure an anonymous guest session exists (zero-friction "just click Start"). */
export async function ensureGuest() {
  const existing = getGuestToken();
  if (existing) return existing;
  const res = await postJSON(ENDPOINTS.auth.guest, {});
  setGuestToken(res.guest_token);
  return res.guest_token;
}

export function me() {
  return getJSON(ENDPOINTS.users.me);
}

/** Re-parent a just-finished guest's activity onto the now-registered account. */
async function claimGuestActivity() {
  const guest = getGuestToken();
  if (!guest) return;
  try {
    await postJSON(ENDPOINTS.auth.claim, { guest_token: guest });
  } catch {
    /* non-fatal: nothing to claim, or already claimed */
  }
}
