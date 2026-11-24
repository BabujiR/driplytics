import { describe, expect, it } from "vitest";

import { fromBase64Url, pkceChallenge, seal, toBase64Url, unseal } from "./crypto";
import { toSession } from "./oidc";
import { type Session, needsRefresh, readSealedSession, safeNext, sessionChunks, sessionMaxAge } from "./session";

const SECRET = "test-secret-that-is-at-least-32-characters";

describe("sealed cookies", () => {
  it("round-trips a value", async () => {
    const sealed = await seal({ at: "token", exp: 1 }, SECRET);
    expect(await unseal(sealed, SECRET)).toEqual({ at: "token", exp: 1 });
  });

  it("rejects tampering, another secret and garbage", async () => {
    const sealed = await seal({ at: "token" }, SECRET);
    const [iv, ct] = sealed.split(".");
    const flipped = `${iv}.${ct!.slice(0, -2)}${ct!.endsWith("A") ? "B" : "A"}${ct!.slice(-1)}`;
    expect(await unseal(flipped, SECRET)).toBeNull();
    expect(await unseal(sealed, `${SECRET}-other`)).toBeNull();
    expect(await unseal("not-a-cookie", SECRET)).toBeNull();
    expect(await unseal(undefined, SECRET)).toBeNull();
  });

  it("splits a large session across cookies and joins it back", async () => {
    const big = await seal({ at: "x".repeat(5000) }, SECRET);
    const chunks = sessionChunks(big);
    expect(chunks.filter(([, v]) => v).length).toBe(2);
    const jar = new Map(chunks.filter(([, v]) => v));
    const joined = readSealedSession({ get: (n) => (jar.has(n) ? { value: jar.get(n)! } : undefined) });
    expect(joined).toBe(big);
    expect(await unseal(joined, SECRET)).toEqual({ at: "x".repeat(5000) });
  });
});

describe("PKCE", () => {
  it("matches the RFC 7636 example", async () => {
    expect(await pkceChallenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")).toBe(
      "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    );
  });

  it("base64url round-trips", () => {
    const bytes = new Uint8Array([0, 251, 255, 62, 63, 1]);
    expect(Array.from(fromBase64Url(toBase64Url(bytes)))).toEqual(Array.from(bytes));
  });
});

describe("session", () => {
  const s: Session = { at: "a", rt: "r", exp: 1000, rexp: 5000 };

  it("refreshes a minute before the access token expires", () => {
    expect(needsRefresh(s, 900)).toBe(false);
    expect(needsRefresh(s, 941)).toBe(true);
  });

  it("lives as long as the refresh token", () => {
    expect(sessionMaxAge(s, 1000)).toBe(4000);
    expect(toSession({ access_token: "a", expires_in: 900, refresh_expires_in: 1800 }, 100)).toEqual({
      at: "a",
      exp: 1000,
      rexp: 1900,
    });
  });

  it("only redirects to local paths after sign-in", () => {
    expect(safeNext("/data/imports?x=1")).toBe("/data/imports?x=1");
    expect(safeNext("https://evil.test")).toBe("/");
    expect(safeNext("//evil.test")).toBe("/");
    expect(safeNext("/\\evil.test")).toBe("/");
    expect(safeNext("/auth/logout")).toBe("/");
    expect(safeNext(null)).toBe("/");
  });
});
