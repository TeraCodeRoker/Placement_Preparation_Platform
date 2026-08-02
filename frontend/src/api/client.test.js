import { beforeEach, describe, expect, it, vi } from "vitest";
import { postJSON, setAccessToken } from "./client";

describe("client refresh-on-401", () => {
  beforeEach(() => {
    setAccessToken(null);
    document.cookie = "";
    vi.restoreAllMocks();
  });

  it("refreshes once on 401, then retries the original request", async () => {
    const hits = [];
    global.fetch = vi.fn(async (u) => {
      hits.push(u);
      if (u.endsWith("/auth/refresh")) {
        return { ok: true, status: 200, json: async () => ({ access_token: "new-token" }) };
      }
      const thingCalls = hits.filter((h) => h.endsWith("/thing")).length;
      if (thingCalls === 1) {
        return { ok: false, status: 401, json: async () => ({ error: { message: "unauth" } }) };
      }
      return { ok: true, status: 200, json: async () => ({ ok: 1 }) };
    });

    const res = await postJSON("/thing", {});
    expect(res).toEqual({ ok: 1 });
    expect(hits.filter((h) => h.endsWith("/auth/refresh"))).toHaveLength(1);
  });

  it("throws a readable error when refresh also fails", async () => {
    global.fetch = vi.fn(async (u) => {
      if (u.endsWith("/auth/refresh")) return { ok: false, status: 401, json: async () => ({}) };
      return { ok: false, status: 401, json: async () => ({ error: { message: "denied" } }) };
    });
    await expect(postJSON("/thing", {})).rejects.toThrow("denied");
  });

  it("does not attempt to refresh the refresh call itself", async () => {
    let refreshCalls = 0;
    global.fetch = vi.fn(async (u) => {
      if (u.endsWith("/auth/refresh")) {
        refreshCalls += 1;
        return { ok: false, status: 401, json: async () => ({}) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    });
    await postJSON("/auth/refresh", {}).catch(() => {});
    expect(refreshCalls).toBe(1); // no recursive refresh
  });
});
