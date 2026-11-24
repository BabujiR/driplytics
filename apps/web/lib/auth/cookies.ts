/** Writing the session to Next's cookie stores (middleware, route handlers). */
import type { NextResponse } from "next/server";

import { authConfig } from "./config";
import { type Session, cookieOptions, sealSession, sessionChunks, sessionMaxAge } from "./session";

type ResponseCookies = NextResponse["cookies"];

export async function writeSession(cookies: ResponseCookies, session: Session): Promise<Array<[string, string]>> {
  const cfg = authConfig();
  const chunks = sessionChunks(await sealSession(session, cfg.sessionSecret));
  const maxAge = sessionMaxAge(session);
  for (const [name, value] of chunks) {
    cookies.set(name, value, cookieOptions(cfg.secureCookies, value ? maxAge : 0));
  }
  return chunks;
}

export function clearSession(cookies: ResponseCookies): void {
  const cfg = authConfig();
  for (const [name] of sessionChunks("")) cookies.set(name, "", cookieOptions(cfg.secureCookies, 0));
}
