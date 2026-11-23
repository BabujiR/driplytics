// Liveness endpoint for the web container's health check.
export function GET() {
  return Response.json({ status: "ok", service: "driplytics-web" });
}
