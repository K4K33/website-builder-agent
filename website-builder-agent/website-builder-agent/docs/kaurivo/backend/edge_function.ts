// Deploy only to a dedicated KAURIVO Supabase project after organization approval.
// Supabase Edge Function name: kaurivo-feedback-submit
// verify_jwt: false, because legitimate customer visitors have no Supabase login.
// Security comes from an opaque, cryptographically random one-use invitation
// token checked server-side against an expiring SHA-256 hash in private tables.
// NEVER put a service_role/secret key in GitHub Pages JavaScript.

const trustedOrigin = "https://k4k33.github.io";
const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

function headers() {
  return {
    "Access-Control-Allow-Origin": trustedOrigin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Vary": "Origin",
    "X-Content-Type-Options": "nosniff",
  };
}
function answer(status: number, body: Record<string, unknown>) {
  return new Response(JSON.stringify(body), { status, headers: headers() });
}
function toHex(bytes: ArrayBuffer) {
  return Array.from(new Uint8Array(bytes)).map(x => x.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async req => {
  const origin = req.headers.get("Origin");
  if (origin !== trustedOrigin) return answer(403, { success: false, error: "origin" });
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: headers() });
  if (req.method !== "POST") return answer(405, { success: false, error: "method" });

  const size = Number(req.headers.get("content-length") ?? "0");
  if (size > 8000) return answer(413, { success: false, error: "size" });
  if (!req.headers.get("content-type")?.startsWith("application/json")) {
    return answer(415, { success: false, error: "format" });
  }
  if (!supabaseUrl || !serviceRole) {
    return answer(503, { success: false, error: "unavailable" });
  }

  let submission: Record<string, unknown>;
  try {
    const raw = await req.text();
    if (raw.length > 8000) return answer(413, { success: false, error: "size" });
    submission = JSON.parse(raw);
    if (!submission || typeof submission !== "object" || Array.isArray(submission)) {
      throw new Error("invalid");
    }
  } catch (_) {
    return answer(400, { success: false, error: "invalid" });
  }

  const token = submission.invitation;
  const rating = submission.rating;
  const message = submission.message;
  const email = submission.email;
  const company = submission.company;
  // A 32-byte base64url token has 43 characters. Never accept human names or
  // email addresses as proof of a sale/invitation.
  if (typeof token !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(token) ||
      !Number.isInteger(rating) || (rating as number) < 1 || (rating as number) > 5 ||
      typeof message !== "string" || message.trim().length < 3 || message.trim().length > 2000 ||
      typeof email !== "string" || email.trim().length > 254 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) ||
      typeof company !== "string" || company.trim().length < 1 || company.trim().length > 120) {
    return answer(400, { success: false, error: "invalid" });
  }

  const digest = toHex(await crypto.subtle.digest(
    "SHA-256", new TextEncoder().encode(token)
  ));
  // Privileged transactional RPC; the service key stays server-side.
  // Token expiration and one-time use are checked inside the database.
  try {
    const result = await fetch(
      supabaseUrl + "/rest/v1/rpc/kaurivo_submit_invited_feedback_v2",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: serviceRole,
          Authorization: "Bearer " + serviceRole,
        },
        body: JSON.stringify({
          p_token_sha256: digest,
          p_rating: rating,
          p_comment: message.trim(),
          p_email: email.trim(),
          p_company: company.trim(),
        }),
      }
    );
    if (!result.ok) return answer(503, { success: false, error: "unavailable" });
    const consumed = await result.json();
    if (consumed !== true) {
      return answer(400, { success: false, error: "invalid_or_used" });
    }
    return answer(200, { success: true });
  } catch (_) {
    // Do not log submission, invitation token, service key or person data.
    return answer(503, { success: false, error: "unavailable" });
  }
});
