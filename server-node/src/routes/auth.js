import { Router } from 'express';
import jwt from 'jsonwebtoken';
import { getFirebase } from '../config/firebase.js';
import { upsertUser } from '../db/pool.js';

const router = Router();

function signAppToken(user) {
  const payload = { sub: user.uid, uid: user.uid, id: user.id };
  const secret = process.env.APP_JWT_SECRET;
  const expiresIn = process.env.APP_JWT_EXPIRES || '7d';
  return jwt.sign(payload, secret, { expiresIn });
}

router.post('/verify', async (req, res) => {
  try {
    const { idToken, displayName, photoURL } = req.body;
    if (!idToken) return res.status(400).json({ error: 'idToken required from Firebase client SDK' });

    const admin = getFirebase();
    const decoded = await admin.auth().verifyIdToken(idToken);
    // decoded fields: uid, email, phone_number, firebase.sign_in_provider
    const user = await upsertUser({
      uid: decoded.uid,
      email: decoded.email || null,
      phone: decoded.phone_number || null,
      name: decoded.name || displayName || null,
      photo_url: decoded.picture || photoURL || null,
      provider: decoded.firebase?.sign_in_provider || 'unknown',
    });

    const token = signAppToken(user);
    res.json({ token, user });
  } catch (e) {
    console.error(e);
    res.status(401).json({ error: 'Invalid token', details: e.message });
  }
});

router.get('/me', (req, res) => {
  try {
    const header = req.headers.authorization || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;
    if (!token) return res.status(401).json({ error: 'Missing bearer token' });
    const payload = jwt.verify(token, process.env.APP_JWT_SECRET);
    res.json({ ok: true, auth: payload });
  } catch (e) {
    return res.status(401).json({ error: 'Invalid token', details: e.message });
  }
});

export default router;
