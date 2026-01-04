import React, { useState } from 'react';
import { Pill, Menu, X } from 'lucide-react';

const Navbar = ({ scrolled }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-md shadow-lg' : 'bg-white/80 backdrop-blur-sm'}`}>
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
              <Pill className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                PharmAgent AI
              </h1>
              <p className="text-xs text-gray-600">Smart Pharmacy System</p>
            </div>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-gray-700 hover:text-emerald-600 font-medium transition">Features</a>
            <a href="#how" className="text-gray-700 hover:text-emerald-600 font-medium transition">How It Works</a>
            <a href="#tech" className="text-gray-700 hover:text-emerald-600 font-medium transition">Technology</a>
            <button className="px-6 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium hover:shadow-lg transition">
              Get Started
            </button>
          </nav>

          <button className="md:hidden" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {menuOpen && (
          <nav className="md:hidden pt-4 pb-2 flex flex-col gap-4">
            <a href="#features" className="text-gray-700 hover:text-emerald-600 font-medium">Features</a>
            <a href="#how" className="text-gray-700 hover:text-emerald-600 font-medium">How It Works</a>
            <a href="#tech" className="text-gray-700 hover:text-emerald-600 font-medium">Technology</a>
            <button className="px-6 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium w-full">
              Get Started
            </button>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Navbar;