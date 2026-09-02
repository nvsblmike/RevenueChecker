import type { NextApiRequest, NextApiResponse } from "next";

export const config = {
  api: {
    bodyParser: { sizeLimit: "1mb" },
    responseLimit: false,
  },
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ detail: "Method not allowed" });
  }

  const backendBaseUrl = process.env.INTERNAL_API_BASE_URL || "http://127.0.0.1:8000";

  try {
    const upstream = await fetch(`${backendBaseUrl}/api`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(typeof req.headers.authorization === "string"
          ? { Authorization: req.headers.authorization }
          : {}),
      },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(180_000),
    });

    const responseBody = await upstream.text();
    res.status(upstream.status);
    res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
    return res.send(responseBody);
  } catch (error) {
    console.error("RevenueCheck API relay failed", error);
    return res.status(504).json({
      detail: "The assessment service took too long to respond. Please try again.",
    });
  }
}
