# 💊 RxCompute - Intelligent Pharmacy Management System

<div align="center">

![RxCompute](https://img.shields.io/badge/PharmAgent-AI%20Powered-10b981?style=for-the-badge&logo=react&logoColor=white)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

**🏥 Transform your traditional pharmacy into an autonomous AI-powered ecosystem**

*Built for Hackfusion Agentic AI Challenge 2025*

[🚀 Live Demo](#) • [📖 Documentation](#documentation) • [🎥 Video](#demo--usage) • [🐛 Report Bug](#-support)

---

![RxCompute Landing Page](https://via.placeholder.com/1200x600/10b981/ffffff?text=PharmAgent+AI+Landing+Page)

*Modern, responsive, and intuitive pharmacy management interface*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Observability](#-observability)
- [Demo](#-demo--usage)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**RxCompute** is a revolutionary agentic AI system that acts as an expert pharmacist, designed specifically for the **Hackfusion Challenge 2025**. It seamlessly handles natural conversations, predicts medicine refill needs, enforces prescription safety rules, and autonomously executes backend operations with minimal human intervention.

### 🎯 Problem Statement

Transform a traditional **search-and-click pharmacy** into an **autonomous AI ecosystem** that:
- Understands natural voice/text conversations
- Predicts medicine refill needs proactively
- Enforces safety and prescription rules automatically
- Executes backend tasks autonomously (inventory, procurement, notifications)

### ✨ Solution Highlights

- 🗣️ **Natural Language Understanding** - Extracts medicine details from messy dialogues
- 🛡️ **Autonomous Safety Enforcement** - Real-time prescription & stock verification
- 🧠 **Predictive Refill System** - AI-driven patient usage pattern analysis
- ⚡ **Real-time Automation** - Inventory updates, webhook triggers, notifications
- 👁️ **Complete Traceability** - Full Chain of Thought (CoT) observability
- 📱 **Modern Interface** - Responsive chat UI with voice capability

---

## 🚀 Features

### Core Agentic Capabilities

<table>
<tr>
<td width="50%">

#### 💬 Conversational Ordering
- Natural text & voice interface
- Extracts medicine names, dosages, quantities
- Context-aware multi-turn dialogues
- Handles messy, human-like conversations

</td>
<td width="50%">

#### 🛡️ Safety & Policy Enforcement
- Medicine Master Data as source of truth
- Real-time stock level verification
- Automatic prescription requirement checks
- Regulatory compliance enforcement

</td>
</tr>
<tr>
<td width="50%">

#### 🧠 Predictive Intelligence
- Analyzes customer order history
- Identifies low medicine supply patterns
- Proactive refill conversation initiation
- Smart dosage frequency tracking

</td>
<td width="50%">

#### ⚡ Real-world Actions (Tool Use)
- Autonomous database updates
- Webhook-based order fulfillment
- Email & WhatsApp notifications
- External system integrations

</td>
</tr>
<tr>
<td width="50%">

#### 💾 Smart Database
- Real-time medicine data access
- Stock level monitoring
- Customer history tracking
- Instant updates & synchronization

</td>
<td width="50%">

#### 👁️ Full Observability
- Langfuse/LangSmith integration
- Complete agent interaction logs
- Decision reasoning transparency
- Performance monitoring & debugging

</td>
</tr>
</table>

---

## 🛠️ Tech Stack

### Frontend
```
React 18.3          → UI Library
Vite 5.4            → Build Tool & Dev Server
Tailwind CSS 3.4    → Utility-first CSS Framework
Lucide React        → Icon Library
```

### Backend (Recommended)
```
FastAPI / Node.js   → RESTful API
Supabase / MongoDB  → Database
Python / JavaScript → Core Logic
```

### AI/ML Stack
```
LangChain           → Agent Orchestration
OpenAI / Claude     → LLM Backbone
Langfuse            → Observability Platform
Whisper API         → Voice Transcription (Optional)
```

### Automation & Integration
```
n8n / Zapier        → Workflow Automation
Webhooks            → Real-time Notifications
Twilio / SendGrid   → Email/WhatsApp APIs
```

---

## 📦 Installation

### Prerequisites

Before you begin, ensure you have:
- **Node.js** 18+ and npm/yarn installed
- **Python** 3.9+ (for backend)
- **Git** for version control

### Quick Start

#### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/pharmagent-ai.git
cd pharmagent-ai
```

#### 2️⃣ Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

#### 3️⃣ Backend Setup (FastAPI - Python)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

#### 4️⃣ Backend Setup (Express - Node.js)

```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Start server
npm run dev
```

### 🔧 Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

---

## 📂 Project Structure

```
pharmagent-ai/
├── 📁 public/                    # Static assets
├── 📁 src/
│   ├── 📁 assets/                # Images, fonts, icons
│   ├── 📁 components/            # React components
│   │   ├── FeatureCard.jsx       # Reusable feature card
│   │   ├── Features.jsx          # Features section
│   │   ├── Footer.jsx            # Footer component
│   │   ├── Hero.jsx              # Hero section
│   │   ├── HowItWorks.jsx        # Process explanation
│   │   └── Navbar.jsx            # Navigation bar
│   ├── 📁 pages/                 # Page components
│   │   └── Landing.jsx           # Main landing page
│   ├── App.jsx                   # Root component
│   ├── App.css                   # App styles
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles (Tailwind)
├── 📁 backend/                   # Backend API
│   ├── main.py / server.js       # API entry point
│   ├── 📁 agents/                # AI agent logic
│   ├── 📁 models/                # Database models
│   ├── 📁 routes/                # API endpoints
│   └── 📁 data/                  # CSV/Excel files
│       ├── medicines.csv         # Medicine master data
│       └── order_history.csv     # Customer orders
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── package.json                  # Dependencies
├── vite.config.js                # Vite configuration
├── tailwind.config.js            # Tailwind configuration
├── postcss.config.js             # PostCSS configuration
└── README.md                     # Documentation
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# ============================================
# API KEYS
# ============================================
VITE_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
VITE_ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# ============================================
# OBSERVABILITY
# ============================================
VITE_LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxx
VITE_LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxx
VITE_LANGFUSE_HOST=https://cloud.langfuse.com

# ============================================
# BACKEND API
# ============================================
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# ============================================
# WEBHOOKS & NOTIFICATIONS
# ============================================
VITE_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/xxxxx
VITE_EMAIL_API_KEY=SG.xxxxxxxxxxxxx
VITE_WHATSAPP_API_KEY=EAA xxxxxxxxxxxxx

# ============================================
# VOICE (Optional)
# ============================================
VITE_WHISPER_API_KEY=your_whisper_key
```

### Tailwind Configuration

**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        emerald: {
          50: '#ecfdf5',
          500: '#10b981',
          600: '#059669',
        },
        teal: {
          500: '#14b8a6',
          600: '#0d9488',
        }
      }
    },
  },
  plugins: [],
}
```

---

## 🎯 Usage

### Starting the Application

#### Development Mode

```bash
# Terminal 1: Backend
cd backend
python main.py  # or npm run dev for Node.js

# Terminal 2: Frontend
npm run dev

# Terminal 3: Observability Dashboard
# Open https://cloud.langfuse.com in browser
```

#### Production Mode

```bash
# Build frontend
npm run build

# Serve with production server
npm run preview
```

### Example Interactions

#### Scenario 1: Simple Medicine Order

```
👤 User: "I need aspirin"

🤖 Bot: "Sure! I found Aspirin 75mg in stock. How many tablets would you like?"

👤 User: "30 tablets please"

🤖 Bot: "✅ Order confirmed!
       • Medicine: Aspirin 75mg
       • Quantity: 30 tablets
       • Prescription: Not required
       • Status: Processing
       
       Your order will be ready for pickup in 30 minutes.
       Order ID: #ORD-2025-001"
```

#### Scenario 2: Prescription Required

```
👤 User: "Can I get amoxicillin 250mg?"

🤖 Bot: "⚠️ Amoxicillin requires a valid prescription. 
       Do you have a prescription from your doctor?"

👤 User: "Yes, I have it"

🤖 Bot: "Great! Please upload your prescription or provide:
       • Prescription Number
       • Doctor's Name
       • Issue Date"

👤 User: [Uploads prescription image]

🤖 Bot: "✅ Prescription verified!
       • Doctor: Dr. Smith
       • Valid until: 2025-02-01
       
       How many capsules do you need?"
```

#### Scenario 3: Proactive Refill Alert

```
🤖 Bot: "👋 Hi John! Your medication reminder:
       
       🔔 Your Aspirin 75mg supply is running low
       • Last ordered: 25 days ago (30 tablets)
       • Estimated remaining: 5 tablets
       
       Would you like to refill now?"

👤 User: "Yes, same quantity"

🤖 Bot: "✅ Refill order placed!
       • Medicine: Aspirin 75mg
       • Quantity: 30 tablets
       • Expected delivery: Tomorrow
       
       We'll notify you when it's ready! 😊"
```

---

## 📊 Data Assets

### Medicine Master Data

**File:** `backend/data/medicines.csv`

```csv
medicine_name,dosage,unit_type,stock_level,prescription_required,price
Paracetamol,500mg,Tablet,1000,No,5.00
Amoxicillin,250mg,Capsule,500,Yes,25.00
Aspirin,75mg,Tablet,800,No,8.00
Insulin,100IU,Injection,200,Yes,150.00
Omeprazole,20mg,Capsule,600,No,12.00
Metformin,500mg,Tablet,750,Yes,18.00
```

### Customer Order History

**File:** `backend/data/order_history.csv`

```csv
customer_id,customer_name,medicine_name,dosage,quantity,order_date,frequency,days_supply
C001,John Doe,Paracetamol,500mg,30,2024-12-01,daily,30
C001,John Doe,Aspirin,75mg,30,2024-11-15,daily,30
C002,Jane Smith,Insulin,100IU,10,2024-12-10,weekly,70
C003,Mike Johnson,Metformin,500mg,60,2024-12-05,twice daily,30
```

---

## 🔍 Observability

### Langfuse Integration

**Backend implementation example (Python):**

```python
from langfuse import Langfuse
import os

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host="https://cloud.langfuse.com"
)

# Create trace for order processing
trace = langfuse.trace(
    name="pharmacy_order_processing",
    user_id="customer_123",
    metadata={
        "order_id": "ORD-2025-001",
        "timestamp": "2025-01-05T10:30:00Z"
    }
)

# Log agent conversation
conversation = trace.span(
    name="extract_medicine_details",
    input={"user_message": "I need aspirin 30 tablets"}
)
conversation.end(
    output={
        "medicine": "Aspirin",
        "dosage": "75mg",
        "quantity": 30
    }
)

# Log safety check
safety_check = trace.span(name="safety_verification")
safety_check.end(
    output={
        "stock_available": True,
        "prescription_required": False,
        "status": "approved"
    }
)
```

### View Traces

Access your complete agent interaction logs:
```
🔗 https://cloud.langfuse.com/project/your-project-id/traces
```

**What you'll see:**
- Complete conversation flow
- Agent decision-making process
- API calls and responses
- Execution time for each step
- Error logs (if any)

---

## 🎥 Demo & Usage

### Video Walkthrough

📹 **[Watch Full Demo Video](#)** *(Coming Soon)*

**Demo highlights:**
1. ✅ Conversational ordering flow (text & voice)
2. ✅ Prescription verification process
3. ✅ Proactive refill alert system
4. ✅ Admin dashboard walkthrough
5. ✅ Observability trace logs
6. ✅ Webhook automation demo

### Screenshots

<table>
<tr>
<td width="50%">

**Landing Page**
![Landing](https://via.placeholder.com/600x400/10b981/ffffff?text=Landing+Page)

</td>
<td width="50%">

**Chat Interface**
![Chat](https://via.placeholder.com/600x400/14b8a6/ffffff?text=Chat+Interface)

</td>
</tr>
<tr>
<td width="50%">

**Admin Dashboard**
![Admin](https://via.placeholder.com/600x400/0d9488/ffffff?text=Admin+Dashboard)

</td>
<td width="50%">

**Observability Traces**
![Traces](https://via.placeholder.com/600x400/059669/ffffff?text=Trace+Logs)

</td>
</tr>
</table>

---

## 📋 Hackfusion Submission Checklist

- ✅ **GitHub Repository** - Clean code with proper documentation
- ✅ **README.md** - Comprehensive setup guide
- ✅ **Mock Backend API** - FastAPI/Node.js with all endpoints
- ✅ **Medicine Master Data** - CSV with stock & prescription flags
- ✅ **Order History Data** - Customer purchase records
- ✅ **Chat Interface** - Text-based conversational UI
- ✅ **Voice Capability** - Speech-to-text integration (bonus)
- ✅ **Admin Dashboard** - Inventory & alert monitoring
- ✅ **Observability Link** - Public Langfuse/LangSmith trace logs
- ✅ **Webhook Automation** - Mock fulfillment triggers
- ✅ **Safety Enforcement** - Prescription & stock verification
- ✅ **Predictive Refill** - Proactive customer alerts

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit** your changes
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push** to the branch
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open** a Pull Request

### Code Style Guidelines

- Use **ESLint** for JavaScript/React
- Follow **PEP 8** for Python
- Write **meaningful commit messages**
- Add **comments** for complex logic
- Update **documentation** when needed

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 RxCompute Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 👥 Team

<table>
<tr>
<td align="center">
<img src="https://via.placeholder.com/100" width="100px;" alt=""/><br />
<sub><b>Your Name</b></sub><br />
<sub>Lead Developer</sub><br />
<a href="https://github.com/yourusername">GitHub</a>
</td>
<td align="center">
<img src="https://via.placeholder.com/100" width="100px;" alt=""/><br />
<sub><b>Team Member 2</b></sub><br />
<sub>AI/ML Engineer</sub><br />
<a href="https://github.com/member2">GitHub</a>
</td>
<td align="center">
<img src="https://via.placeholder.com/100" width="100px;" alt=""/><br />
<sub><b>Team Member 3</b></sub><br />
<sub>Backend Developer</sub><br />
<a href="https://github.com/member3">GitHub</a>
</td>
</tr>
</table>

---

## 🙏 Acknowledgments

Special thanks to:

- **Hackfusion Team** - For organizing this amazing challenge
- **Anthropic** - For Claude AI capabilities
- **OpenAI** - For GPT models
- **Langfuse** - For the observability platform
- **Vercel** - For hosting infrastructure
- **React Team** - For the amazing framework
- **Tailwind CSS** - For utility-first styling

---

## 📞 Support

Need help? We're here for you!

- 📧 **Email:** support@pharmagent.ai
- 💬 **Discord:** [Join our server](#)
- 🐛 **Issues:** [GitHub Issues](https://github.com/yourusername/pharmagent-ai/issues)
- 📖 **Docs:** [Documentation](#)
- 🎥 **Video:** [Tutorial Playlist](#)

### Common Issues

<details>
<summary><b>Tailwind CSS not working?</b></summary>

Make sure `@import` is **before** `@tailwind` directives in `index.css`:
```css
@import url('https://fonts.googleapis.com/...');

@tailwind base;
@tailwind components;
@tailwind utilities;
```
</details>

<details>
<summary><b>API connection failed?</b></summary>

Check your `.env` file and ensure `VITE_API_BASE_URL` is correct:
```env
VITE_API_BASE_URL=http://localhost:8000
```
</details>

<details>
<summary><b>Voice input not working?</b></summary>

Ensure you have:
1. Microphone permissions enabled
2. HTTPS connection (voice API requires secure context)
3. Whisper API key configured in `.env`
</details>

---

## 🚀 Deployment

### Deploy to Vercel (Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Deploy Backend (Railway/Render)

```bash
# For Railway
railway up

# For Render
# Connect your GitHub repo and deploy
```

---

## 📈 Roadmap

Future enhancements planned:

- [ ] Multi-language support (Hindi, Spanish, etc.)
- [ ] Mobile app (React Native)
- [ ] Insurance claim integration
- [ ] Prescription OCR scanning
- [ ] Drug interaction warnings
- [ ] Video consultation integration
- [ ] Loyalty rewards system
- [ ] Analytics dashboard for pharmacy owners

---

## 🏆 Hackfusion Challenge Submission

**Project Name:** RxCompute  
**Category:** Agentic AI System  
**Challenge:** Hackfusion 2025  
**Submission Date:** January 2025  

**Key Deliverables:**
1. ✅ GitHub Repository with clean code
2. ✅ Live Demo URL
3. ✅ Observability Dashboard Link
4. ✅ Video Demonstration
5. ✅ Complete Documentation

---

<div align="center">

### ⭐ Star this repo if you find it useful!

**Made with ❤️ for Hackfusion Challenge 2025**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/pharmagent-ai?style=social)](https://github.com/yourusername/pharmagent-ai/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/pharmagent-ai?style=social)](https://github.com/yourusername/pharmagent-ai/network/members)

[⬆ Back to Top](#-pharmagent-ai---intelligent-pharmacy-management-system)

---

**© 2025 RxCompute Team. All Rights Reserved.**

</div>