function env() {
  return {
    url: process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL,
    token: process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN
  }
}

async function redisGet(key) {
  const { url, token } = env()
  if (!url || !token) throw new Error("Demo storage not configured")
  const r = await fetch(`${url}/get/${encodeURIComponent(key)}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const j = await r.json()
  return j.result
}

export default async function handler(req, res) {
  try {
    const id = String(req.query.id || "")
    const side = req.query.side === "right" ? "right" : "left"

    if (!/^[a-zA-Z0-9_-]{8,80}$/.test(id)) {
      return res.status(400).send("Invalid demo id")
    }

    let value = "iana"

    if (side === "right") {
      const stored = await redisGet(`splitsignal:demo:${id}`)
      value = stored === "changed" ? "changed" : "iana"
    }

    res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate")
    res.setHeader("Content-Type", "text/html; charset=utf-8")

    return res.status(200).send(`<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>SplitSignal Demo Source</title>
  <style>
    body{
      font-family:Arial,sans-serif;
      background:#0b0c0b;
      color:#f2eee5;
      padding:48px;
    }
    .tag{
      color:#ff5c00;
      font-size:12px;
      text-transform:uppercase;
      letter-spacing:.12em;
    }
    h1{font-size:42px;margin:12px 0}
    .value{
      font-family:monospace;
      font-size:28px;
      border:1px solid #333;
      border-radius:16px;
      padding:20px;
      margin-top:20px;
      display:inline-block;
    }
  </style>
</head>
<body>
  <div class="tag">SplitSignal Public Demo Source</div>
  <h1>Source ${side === "left" ? "A" : "B"}</h1>
  <div class="value">${value}</div>
</body>
</html>`)
  } catch (e) {
    return res.status(500).send("Demo source unavailable")
  }
}
