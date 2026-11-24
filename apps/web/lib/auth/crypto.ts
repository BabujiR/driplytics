/**
 * Small Web Crypto helpers that run in both the Edge runtime (middleware) and Node (route handlers).
 * No dependencies: AES-256-GCM for sealed cookies, SHA-256 for PKCE.
 */

const enc = new TextEncoder();
const dec = new TextDecoder();

export function toBase64Url(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function fromBase64Url(text: string) {
  const s = atob(text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4));
  return Uint8Array.from(s, (c) => c.charCodeAt(0));
}

export function randomToken(bytes = 32): string {
  return toBase64Url(crypto.getRandomValues(new Uint8Array(bytes)));
}

/** PKCE S256 code challenge for a verifier (RFC 7636). */
export async function pkceChallenge(verifier: string): Promise<string> {
  return toBase64Url(new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(verifier))));
}

const keys = new Map<string, Promise<CryptoKey>>();

function aesKey(secret: string): Promise<CryptoKey> {
  let key = keys.get(secret);
  if (!key) {
    key = crypto.subtle
      .digest("SHA-256", enc.encode(secret))
      .then((raw) => crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]));
    keys.set(secret, key);
  }
  return key;
}

/** Encrypt and authenticate a JSON value: "<iv>.<ciphertext>" in base64url. */
export async function seal(value: unknown, secret: string): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = enc.encode(JSON.stringify(value));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await aesKey(secret), data));
  return `${toBase64Url(iv)}.${toBase64Url(ct)}`;
}

/** The value, or null if the text was tampered with, truncated or sealed with another secret. */
export async function unseal<T>(text: string | undefined, secret: string): Promise<T | null> {
  if (!text) return null;
  const [iv, ct] = text.split(".");
  if (!iv || !ct) return null;
  try {
    const plain = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: fromBase64Url(iv) },
      await aesKey(secret),
      fromBase64Url(ct),
    );
    return JSON.parse(dec.decode(plain)) as T;
  } catch {
    return null;
  }
}
