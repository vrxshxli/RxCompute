import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { initFirebase } from './config/firebase.js';
import authRouter from './routes/auth.js';

initFirebase();

const app = express();
app.use(helmet());
app.use(cors({ origin: '*', credentials: true }));
app.use(express.json());
app.use(morgan('dev'));

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'pharmaforge-auth-node' });
});

app.use('/auth', authRouter);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Node auth server listening on :${PORT}`);
});
