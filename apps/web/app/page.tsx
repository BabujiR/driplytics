import { isReady, type ReadinessResponse } from "@driplytics/contracts";
import { brand } from "@driplytics/ui";

// Always render on request so the status reflects the live stack.
export const dynamic = "force-dynamic";

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

async function getReadiness(): Promise<ReadinessResponse | null> {
  try {
    const res = await fetch(`${API_URL}/health/ready`, { cache: "no-store" });
    return (await res.json()) as ReadinessResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const readiness = await getReadiness();
  return (
    <main>
      <h1>💧 {brand.name}</h1>
      <p>{brand.tagline}</p>
      <h2>Phase 0 stack status</h2>
      {readiness === null ? (
        <p className="bad">API not reachable at {API_URL}. Is the api container running?</p>
      ) : (
        <>
          <p className={isReady(readiness) ? "ok" : "bad"}>
            API is {isReady(readiness) ? "ready" : "degraded"}
          </p>
          <table>
            <thead>
              <tr>
                <th>Dependency</th>
                <th>Status</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(readiness.checks).map(([name, check]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td className={check.ok ? "ok" : "bad"}>{check.ok ? "OK" : "Down"}</td>
                  <td>{check.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <p>
        Wireframes: <a href="https://storage.googleapis.com/driplytics-demo/index.html">live demo</a> · API
        docs: <a href="http://localhost:8000/api/docs">localhost:8000/api/docs</a>
      </p>
    </main>
  );
}
