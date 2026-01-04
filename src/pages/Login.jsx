import React, { useState } from 'react';
import { Pill, Phone, ArrowLeft, Mail } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';

const Login = () => {
  const navigate = useNavigate();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [confirmationResult, setConfirmationResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // FastAPI backend base URL
  const API_BASE = 'http://127.0.0.1:8000';

  // Firebase client config (frontend)
  const firebaseConfig = {
    apiKey: 'AIzaSyAKbCaK-IBkfVVBejk3GPq5qNdsT7T6VtA',
    authDomain: 'pharmagent-ai.firebaseapp.com',
    projectId: 'pharmagent-ai',
    storageBucket: 'pharmagent-ai.firebasestorage.app',
    messagingSenderId: '1057060503974',
    appId: '1:1057060503974:web:7008325a96829d24f28f67',
    measurementId: 'G-H1Z7DS5LK6'
  };

  // Initialize Firebase once
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const provider = new GoogleAuthProvider();

  const handleSendOtp = async (e) => {
    e.preventDefault();
    try {
      setErrorMsg('');
      setLoading(true);
      // Ensure number has country code (assume India +91 if not provided)
      let num = phoneNumber.trim();
      if (!num.startsWith('+')) num = '+91' + num.replace(/^0+/, '');

      if (!window.recaptchaVerifier) {
        window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', { size: 'invisible' });
      }
      const appVerifier = window.recaptchaVerifier;
      console.log('Sending OTP to:', num);
      const result = await signInWithPhoneNumber(auth, num, appVerifier);
      setConfirmationResult(result);
      setShowOtpInput(true);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);
      
      // Auto focus next input
      if (value && index < 5) {
        document.getElementById(`otp-${index + 1}`).focus();
      }
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    try {
      setErrorMsg('');
      setLoading(true);
      const otpCode = otp.join('');
      if (!confirmationResult) throw new Error('OTP session expired. Please resend OTP.');
      const credResult = await confirmationResult.confirm(otpCode);
      const idToken = await credResult.user.getIdToken();
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || err.detail || `Login failed (${res.status})`);
      }
      const data = await res.json();
      localStorage.setItem('app_token', data.token);
      const role = (data.user && data.user.role) || 'user';
      redirectByRole(role);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const redirectByRole = (role) => {
    if (role === 'admin') navigate('/dashboard/admin');
    else if (role === 'warehouse') navigate('/dashboard/warehouse');
    else if (role === 'pharmacist') navigate('/dashboard/pharmacist');
    else navigate('/dashboard/user');
  };

  const handleGoogleLogin = async () => {
    try {
      console.log('Google login initiated');
      const result = await signInWithPopup(auth, provider);
      const idToken = await result.user.getIdToken();

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || err.detail || `Login failed (${res.status})`);
      }
      const data = await res.json();
      localStorage.setItem('app_token', data.token);
      const role = (data.user && data.user.role) || 'user';
      redirectByRole(role);
    } catch (e) {
      console.error('Google login error:', e);
      alert(e.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center px-6 py-12 relative overflow-hidden">
      {/* Background Decorations - Fixed */}
      <div className="fixed top-20 left-10 w-72 h-72 bg-emerald-200/30 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed bottom-20 right-10 w-96 h-96 bg-teal-200/30 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="mb-6 flex items-center gap-2 text-gray-600 hover:text-emerald-600 transition"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Home</span>
        </button>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
          {/* Logo & Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Pill className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
            <p className="text-gray-600">Sign in to your PharmAgent account</p>
          </div>

          {/* Error Banner */}
          {errorMsg && (
            <div className="mb-4 px-4 py-3 bg-red-100 text-red-700 rounded">{errorMsg}</div>
          )}

          {/* Google Login Button */}
          <button 
            onClick={handleGoogleLogin}
            className="w-full py-3 px-4 border-2 border-gray-300 rounded-lg hover:bg-gray-50 transition flex items-center justify-center gap-3 mb-6 hover:border-emerald-500 group"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span className="font-semibold text-gray-700 group-hover:text-emerald-600">Continue with Google</span>
          </button>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">Or login with phone</span>
            </div>
          </div>

          {/* reCAPTCHA container (invisible) */}
          <div id="recaptcha-container" />

          {/* Phone Login Form */}
          {!showOtpInput ? (
            <form onSubmit={handleSendOtp} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+91 98765 43210"
                    required
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-semibold hover:shadow-xl hover:shadow-emerald-500/30 transition-all transform hover:scale-[1.02] disabled:opacity-60"
              >
                {loading ? 'Sending OTP...' : 'Send OTP'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 text-center">
                  Enter OTP sent to {phoneNumber}
                </label>
                <div className="flex gap-2 justify-center">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-${index}`}
                      type="text"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      className="w-12 h-12 text-center text-xl font-bold border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition"
                    />
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-semibold hover:shadow-xl hover:shadow-emerald-500/30 transition-all transform hover:scale-[1.02] disabled:opacity-60"
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>

              <button
                type="button"
                onClick={() => setShowOtpInput(false)}
                className="w-full text-emerald-600 hover:text-emerald-700 font-medium text-sm"
              >
                Change phone number
              </button>
            </form>
          )}

          {/* Sign Up Link */}
          <p className="mt-6 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <button 
              onClick={() => navigate('/signup')}
              className="text-emerald-600 hover:text-emerald-700 font-semibold"
            >
              Sign up for free
            </button>
          </p>
        </div>

        {/* Trust Badge */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            🔒 Your data is secure with 256-bit encryption
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
