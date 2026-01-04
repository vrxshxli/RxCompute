import admin from 'firebase-admin';

export function initFirebase() {
  if (admin.apps.length) return admin.app();

  // Prefer JSON in env; fallback to GOOGLE_APPLICATION_CREDENTIALS file path
  const json = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (json) {
    const credObj = JSON.parse(json);
    admin.initializeApp({
      credential: admin.credential.cert(credObj),
    });
  } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    admin.initializeApp({
      credential: admin.credential.applicationDefault(),
    });
  } else {
    throw new Error('Firebase Admin credentials not provided. Set FIREBASE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS');
  }
  return admin.app();
}

export function getFirebase() {
  if (!admin.apps.length) throw new Error('Firebase not initialized');
  return admin;
}
