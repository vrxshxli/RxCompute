import React from 'react';
import { MessageSquare, Brain, CheckCircle, Zap } from 'lucide-react';

const HowItWorks = () => {
  const steps = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: "Customer Speaks",
      description: "Patient requests medicine via chat or voice in natural language"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "AI Processes",
      description: "System extracts details, checks stock, verifies prescription requirements"
    },
    {
      icon: <CheckCircle className="w-8 h-8" />,
      title: "Smart Decision",
      description: "AI approves order based on safety rules and availability"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Auto Execute",
      description: "System updates inventory, triggers fulfillment, sends confirmations"
    }
  ];

  return (
    <section className="py-20 px-6 bg-white">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900">
            How It Works
          </h2>
          <p className="text-xl text-gray-600">
            From conversation to delivery in seconds
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-8 max-w-6xl mx-auto">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center mx-auto mb-4 text-white shadow-lg">
                  {step.icon}
                </div>
                <div className="absolute top-8 left-1/2 w-full h-0.5 bg-gradient-to-r from-emerald-300 to-teal-300 -z-10 hidden md:block" 
                     style={{ display: index === steps.length - 1 ? 'none' : 'block' }}></div>
                <h3 className="text-lg font-bold mb-2 text-gray-900">{step.title}</h3>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;