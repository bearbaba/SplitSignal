function env() {
  return {
    url:
      process.env.UPSTASH_REDIS_REST_KV_REST_API_URL ||
      process.env.UPSTASH_REDIS_REST_URL ||
      process.env.KV_REST_API_URL,
    token:
      process.env.UPSTASH_REDIS_REST_KV_REST_API_TOKEN ||
      process.env.UPSTASH_REDIS_REST_TOKEN ||
      process.env.KV_REST_API_TOKEN
  }
}

async function command(path) {
  const { url, token } = env()
  if (!url || !token) throw new Error("Demo storage not configured")

  const r = await fetch(`${url}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  })

  if (!r.ok) throw new Error("Demo storage unavailable")

  return r.json()
}

async function redisSet(key, value) {
  await command(
    `/set/${encodeURIComponent(key)}/${encodeURIComponent(value)}?EX=86400`
  )
}

async function rateLimit(req) {
  const raw =
    req.headers["x-forwarded-for"] ||
    req.socket?.remoteAddress ||
    "unknown"

  const ip = String(raw).split(",")[0].trim().replace(/[^a-zA-Z0-9:._-]/g, "")
  const key = `splitsignal:rl:${ip}`

  const j = await command(`/incr/${encodeURIComponent(key)}`)
  const n = Number(j.result || 0)

  if (n === 1) {
    await command(`/expire/${encodeURIComponent(key)}/600`)
  }

  return n <= 20
}

export default async function handler(req, res) {
  try {
    if (req.method !== "POST")
      return res.status(405).json({ ok:false })

    if (!(await rateLimit(req)))
      return res.status(429).json({
        ok:false,
        error:"Too many demo requests. Try again in a few minutes."
      })

    const id = String(req.query.id || "")

    if (!/^[a-zA-Z0-9_-]{8,80}$/.test(id))
      return res.status(400).json({ ok:false })

    await redisSet(`splitsignal:demo:${id}`, "changed")

    return res.status(200).json({
      ok:true,
      value:"changed"
    })

  } catch (e) {
    return res.status(500).json({
      ok:false,
      error:e.message
    })
  }
}
