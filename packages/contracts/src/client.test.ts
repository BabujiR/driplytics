import { describe, expect, it } from "vitest";

import { ApiError, createApiClient, errorMessage, isFinished, unwrap, uploadToTarget } from "./client";

type Handler = (req: Request) => Response | Promise<Response>;

function fakeFetch(handler: Handler) {
  const seen: Request[] = [];
  const impl = async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = input instanceof Request ? input : new Request(input, init);
    seen.push(req);
    return handler(req);
  };
  return { impl: impl as typeof globalThis.fetch, seen };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("createApiClient", () => {
  it("sends the token and tenant on every request and returns typed data", async () => {
    const { impl, seen } = fakeFetch(() => json([{ id: "s1", name: "Riverbend WTP" }]));
    const api = createApiClient({
      baseUrl: "http://api.test/",
      getToken: async () => "tok",
      getTenantId: () => "t-1",
      fetch: impl,
    });
    const sites = await unwrap(api.GET("/api/v1/sites"));
    expect(sites[0]?.name).toBe("Riverbend WTP");
    expect(seen[0]?.url).toBe("http://api.test/api/v1/sites");
    expect(seen[0]?.headers.get("Authorization")).toBe("Bearer tok");
    expect(seen[0]?.headers.get("X-Tenant-Id")).toBe("t-1");
  });

  it("fills path parameters", async () => {
    const { impl, seen } = fakeFetch(() => json({ id: "abc" }));
    const api = createApiClient({ baseUrl: "http://api.test", fetch: impl });
    await unwrap(api.GET("/api/v1/imports/{import_id}", { params: { path: { import_id: "abc" } } }));
    expect(seen[0]?.url).toBe("http://api.test/api/v1/imports/abc");
    expect(seen[0]?.headers.get("Authorization")).toBeNull();
  });

  it("throws ApiError with the API's message", async () => {
    const { impl } = fakeFetch(() => json({ detail: "site not found" }, 404));
    const api = createApiClient({ baseUrl: "http://api.test", fetch: impl });
    const call = unwrap(api.GET("/api/v1/sites/{site_id}", { params: { path: { site_id: "x" } } }));
    await expect(call).rejects.toMatchObject({ name: "ApiError", status: 404, message: "site not found" });
  });
});

describe("errorMessage", () => {
  it("joins FastAPI validation issues by field", () => {
    const body = { detail: [{ loc: ["body", "timezone"], msg: "unknown time zone" }, { msg: "bad" }] };
    expect(errorMessage(422, body)).toBe("timezone: unknown time zone; bad");
  });
  it("falls back to the status", () => {
    expect(errorMessage(502, "<html>")).toBe("request failed (HTTP 502)");
  });
});

describe("uploadToTarget", () => {
  it("PUTs the file to the presigned URL", async () => {
    const { impl, seen } = fakeFetch(() => new Response(null, { status: 200 }));
    await uploadToTarget({ url: "http://minio.test/b/k", method: "PUT", headers: {}, expires_in: 900 }, new Blob(["a,b"]), impl);
    expect(seen[0]?.method).toBe("PUT");
    expect(await seen[0]?.text()).toBe("a,b");
  });
  it("throws when storage refuses", async () => {
    const { impl } = fakeFetch(() => new Response("expired", { status: 403 }));
    const target = { url: "http://minio.test/b/k", method: "PUT" as const, headers: {}, expires_in: 900 };
    await expect(uploadToTarget(target, new Blob(["x"]), impl)).rejects.toBeInstanceOf(ApiError);
  });
});

it("isFinished", () => {
  expect(isFinished("running")).toBe(false);
  expect(isFinished("failed")).toBe(true);
});
