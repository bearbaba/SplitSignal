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

async function redisSet(key, value) {
  const { url, token } = env()
  if (!url || !token) throw new Error("Demo storage not configured")
  const r = await fetch(
    `${url}/set/${encodeURIComponent(key)}/${encodeURIComponent(value)}?EX=86400`,
    { headers: { Authorization: `Bearer ${token}` } }
  )
  if (!r.ok) throw new Error("Storage write failed")
}

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") return res.status(405).json({ ok:false })

    const id = String(req.query.id || "")
    if (!/^[a-zA-Z0-9_-]{8,80}$/.test(id)) {
      return res.status(400).json({ ok:false })
    }

    await redisSet(`splitsignal:demo:${id}`, "changed")

    return res.status(200).json({ ok:true, value:"changed" })
  } catch (e) {
    return res.status(500).json({ ok:false, error:e.message })
  }
}
