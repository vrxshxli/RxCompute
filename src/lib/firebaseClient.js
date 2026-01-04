import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: 'AIzaSyAKbCaK-IBkfVVBejk3GPq5qNdsT7T6VtA',
  authDomain: 'pharmagent-ai.firebaseapp.com',
  projectId: 'pharmagent-ai',
  storageBucket: 'pharmagent-ai.firebasestorage.app',
  messagingSenderId: '1057060503974',
  appId: '1:1057060503974:web:7008325a96829d24f28f67',
  measurementId: 'G-H1Z7DS5LK6'
};

// Initialize once for the whole SPA
if (!getApps().length) {
  initializeApp(firebaseConfig);
}

export const auth = getAuth();
