import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Footer from '../components/Footer';
import { Database, Eye, Activity, CheckCircle, Smartphone, Bell, TrendingUp, Stethoscope } from 'lucide-react';

const Landing = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const requirements = [
    { icon: <Database className="w-5 h-5" />, text: "Medicine Master Database", status: "Stock & Prescription Data" },
    { icon: <TrendingUp className="w-5 h-5" />, text: "Order History Analytics", status: "Predictive Refill System" },
    { icon: <Activity className="w-5 h-5" />, text: "FastAPI/Node.js Backend", status: "Real-time Processing" },
    { icon: <Eye className="w-5 h-5" />, text: "Langfuse Observability", status: "Complete Traceability" },
    { icon: <Smartphone className="w-5 h-5" />, text: "Chat + Voice Interface", status: "Multi-modal Input" },
    { icon: <Bell className="w-5 h-5" />, text: "Smart Alert System", status: "Proactive Notifications" }
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navbar scrolled={scrolled} />
      <Hero />
      <Features />
      <HowItWorks />
      
      {/* Tech Stack Section */}
      <section className="py-20 px-6 bg-gradient-to-b from-emerald-50 to-white">
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 text-gray-900">
              Built on Modern Technology
            </h2>
            <p className="text-xl text-gray-600">
              Enterprise-grade infrastructure for reliable pharmacy operations
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {requirements.map((req, index) => (
              <div key={index} className="flex items-center gap-4 p-4 bg-white rounded-xl shadow-md border border-gray-100 hover:border-emerald-300 hover:shadow-lg transition-all">
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center text-white flex-shrink-0">
                  {req.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{req.text}</h4>
                  <p className="text-sm text-gray-600">{req.status}</p>
                </div>
                <CheckCircle className="w-5 h-5 text-emerald-500" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxIDAgNiAyLjY5IDYgNnMtMi42OSA2LTYgNi02LTIuNjktNi02IDIuNjktNiA2LTZ6TTI0IDQyYzMuMzEgMCA2IDIuNjkgNiA2cy0yLjY5IDYtNiA2LTYtMi42OS02LTYgMi42OS02IDYtNnoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4xIiBzdHJva2Utd2lkdGg9IjIiLz48L2c+PC9zdmc+')] opacity-10"></div>
        
        <div className="container mx-auto text-center relative">
          <div className="max-w-3xl mx-auto">
            <Stethoscope className="w-16 h-16 mx-auto mb-6 text-white" />
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Ready to Transform Your Pharmacy?
            </h2>
            <p className="text-xl text-emerald-100 mb-8">
              Join the future of intelligent pharmacy management. Start automating today.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <button className="px-8 py-4 bg-white text-emerald-600 rounded-lg font-semibold text-lg hover:shadow-2xl transition-all transform hover:scale-105">
                Get Started Free
              </button>
              <button className="px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-semibold text-lg hover:bg-white/10 transition-all">
                Schedule Demo
              </button>
            </div>

            <div className="grid md:grid-cols-3 gap-6 text-white">
              <div className="p-4 bg-white/10 backdrop-blur-sm rounded-xl">
                <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                <div className="font-semibold">No Credit Card Required</div>
              </div>
              <div className="p-4 bg-white/10 backdrop-blur-sm rounded-xl">
                <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                <div className="font-semibold">Setup in Minutes</div>
              </div>
              <div className="p-4 bg-white/10 backdrop-blur-sm rounded-xl">
                <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                <div className="font-semibold">24/7 Support</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;