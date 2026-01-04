import React from 'react';
import { MessageSquare, Shield, Brain, Zap, Database, Eye, Pill } from 'lucide-react';
import FeatureCard from './FeatureCard';

const Features = () => {
  const features = [
    {
      icon: <MessageSquare className="w-7 h-7 text-white" />,
      title: "Natural Conversations",
      description: "Talk naturally via text or voice. Our AI understands messy dialogues and extracts medicine details accurately.",
      color: "bg-gradient-to-br from-emerald-500 to-emerald-600"
    },
    {
      icon: <Shield className="w-7 h-7 text-white" />,
      title: "Safety First",
      description: "Automatic prescription verification, stock checks, and policy enforcement to ensure patient safety.",
      color: "bg-gradient-to-br from-teal-500 to-teal-600"
    },
    {
      icon: <Brain className="w-7 h-7 text-white" />,
      title: "Smart Predictions",
      description: "Proactively identifies when patients need refills based on their history and usage patterns.",
      color: "bg-gradient-to-br from-cyan-500 to-cyan-600"
    },
    {
      icon: <Zap className="w-7 h-7 text-white" />,
      title: "Instant Actions",
      description: "Automatically updates inventory, sends confirmations, and triggers fulfillment workflows.",
      color: "bg-gradient-to-br from-emerald-600 to-teal-600"
    },
    {
      icon: <Database className="w-7 h-7 text-white" />,
      title: "Smart Database",
      description: "Real-time access to medicine data, stock levels, and customer history with instant updates.",
      color: "bg-gradient-to-br from-teal-600 to-cyan-600"
    },
    {
      icon: <Eye className="w-7 h-7 text-white" />,
      title: "Full Transparency",
      description: "Complete visibility into AI decision-making with detailed logs and reasoning chains.",
      color: "bg-gradient-to-br from-cyan-600 to-emerald-600"
    }
  ];

  return (
    <section className="py-20 px-6 bg-gradient-to-b from-white to-emerald-50">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 mb-4 px-4 py-2 bg-emerald-100 rounded-full">
            <Pill className="w-4 h-4 text-emerald-600" />
            <span className="text-emerald-800 text-sm font-semibold">Core Capabilities</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900">
            Intelligent Pharmacy Features
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Everything you need to run a modern, efficient, and safe pharmacy operation
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <FeatureCard key={index} {...feature} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;