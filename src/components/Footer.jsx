import React from 'react';
import { Pill, Database, Eye, Activity } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="py-12 px-6 bg-gray-900 text-white">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <Pill className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-lg">RxCompute</div>
              <div className="text-sm text-gray-400">Team Invaders</div>
            </div>
          </div>
          
          <div className="text-center text-gray-400">
            <p>Built with ❤️ for Modern Healthcare</p>
            <p className="text-sm mt-1">Transforming Pharmacies with Intelligent AI</p>
          </div>
          
          <div className="flex gap-4">
            <button className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-emerald-600 transition">
              <Database className="w-5 h-5" />
            </button>
            <button className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-emerald-600 transition">
              <Eye className="w-5 h-5" />
            </button>
            <button className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-emerald-600 transition">
              <Activity className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;