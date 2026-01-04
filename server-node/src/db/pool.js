import pg from 'pg';
const { Pool } = pg;

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.PGSSL === 'true' ? { rejectUnauthorized: false } : false,
});

export async function upsertUser({ uid, email, phone, name, photo_url, provider }) {
  const q = `
  INSERT INTO users (uid, email, phone, name, photo_url, provider)
  VALUES ($1, $2, $3, $4, $5, $6)
  ON CONFLICT (uid) DO UPDATE SET
    email = EXCLUDED.email,
    phone = EXCLUDED.phone,
    name = EXCLUDED.name,
    photo_url = EXCLUDED.photo_url,
    provider = EXCLUDED.provider
  RETURNING id, uid, email, phone, name, photo_url, provider, created_at, updated_at;`;
  const vals = [uid, email, phone, name, photo_url, provider];
  const { rows } = await pool.query(q, vals);
  return rows[0];
}
