import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Navbar = ({ scrolled }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/95 backdrop-blur-md shadow-lg' : 'bg-white/80 backdrop-blur-sm'
      }`}
    >
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo Area */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center gap-3 cursor-pointer select-none"
          >
            {/* RxCompute Logo - Modern SVG */}
            <svg
              width="52"
              height="52"
              viewBox="0 0 52 52"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="flex-shrink-0 drop-shadow-md"
            >
              {/* Background circle with gradient */}
              <circle cx="26" cy="26" r="24" fill="url(#logoGrad)" />
              {/* Stylized Rx pill/capsule shape */}
              <ellipse
                cx="26"
                cy="26"
                rx="16"
                ry="22"
                fill="none"
                stroke="white"
                strokeWidth="5"
                strokeLinecap="round"
              />
              {/* Cross / plus symbol inside */}
              <path
                d="M26 14 L26 38 M14 26 L38 26"
                stroke="white"
                strokeWidth="5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Gradient definition */}
              <defs>
                <linearGradient
                  id="logoGrad"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor="#10b981" /> {/* emerald-500 */}
                  <stop offset="100%" stopColor="#14b8a6" /> {/* teal-600 */}
                </linearGradient>
              </defs>
            </svg>

            {/* Text part */}
            <div className="leading-tight">
              <h1 className="text-2xl md:text-3xl font-extrabold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent tracking-tight">
                RxCompute
              </h1>
              <p className="text-xs text-gray-600 font-medium -mt-1">
                Smart Pharmacy System
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <a
              href="#features"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
            >
              Features
            </a>
            <a
              href="#how"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
            >
              How It Works
            </a>
            <a
              href="#tech"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
            >
              Technology
            </a>
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium hover:shadow-lg hover:shadow-emerald-500/30 transition-all"
            >
              Get Started
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <button className="md:hidden text-gray-700" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X className="w-7 h-7" /> : <Menu className="w-7 h-7" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <nav className="md:hidden pt-6 pb-4 flex flex-col gap-5 border-t border-gray-100 mt-4">
            <a
              href="#features"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="#how"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              How It Works
            </a>
            <a
              href="#tech"
              className="text-gray-700 hover:text-emerald-600 font-medium transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              Technology
            </a>
            <button
              onClick={() => {
                navigate('/login');
                setMenuOpen(false);
              }}
              className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium text-center"
            >
              Get Started
            </button>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Navbar;