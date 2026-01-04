import React from 'react';
import { Activity, Pill, Stethoscope } from 'lucide-react';

const Hero = () => {
  return (
    <section className="relative pt-32 pb-20 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 via-white to-teal-50 -z-10"></div>
      <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-200/30 rounded-full blur-3xl"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-teal-200/30 rounded-full blur-3xl"></div>
      
      <div className="container mx-auto text-center relative">
        <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 bg-emerald-100 rounded-full border border-emerald-300">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span className="text-emerald-800 text-sm font-semibold">AI-Powered Healthcare Innovation</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight text-gray-900">
          Your Pharmacy's
          <br />
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 bg-clip-text text-transparent">
            AI Pharmacist Assistant
          </span>
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
          Transform your pharmacy with an intelligent AI system that understands conversations, 
          predicts refill needs, ensures prescription safety, and automates operations seamlessly.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
          <button className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-semibold text-lg hover:shadow-xl hover:shadow-emerald-500/30 transition-all transform hover:scale-105 flex items-center justify-center gap-2">
            <Pill className="w-5 h-5" />
            Start Free Trial
          </button>
          <button className="px-8 py-4 bg-white border-2 border-emerald-600 text-emerald-600 rounded-lg font-semibold text-lg hover:bg-emerald-50 transition-all flex items-center justify-center gap-2">
            <Stethoscope className="w-5 h-5" />
            Watch Demo
          </button>
        </div>

        <div className="flex flex-wrap justify-center gap-8 text-center">
          <div className="flex flex-col items-center">
            <div className="text-3xl font-bold text-emerald-600">99.9%</div>
            <div className="text-sm text-gray-600">Accuracy Rate</div>
          </div>
          <div className="flex flex-col items-center">
            <div className="text-3xl font-bold text-teal-600">24/7</div>
            <div className="text-sm text-gray-600">AI Availability</div>
          </div>
          <div className="flex flex-col items-center">
            <div className="text-3xl font-bold text-cyan-600">50%</div>
            <div className="text-sm text-gray-600">Time Saved</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;