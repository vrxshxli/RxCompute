import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import UserDashboard from './pages/dashboard/User';
import AdminDashboard from './pages/dashboard/Admin';
import WarehouseDashboard from './pages/dashboard/Warehouse';
import PharmacistDashboard from './pages/dashboard/Pharmacist';
import VoiceAgent from './components/VoiceAgent';
import './App.css';

function App() {
  return (
    <Router>
      {/* Global voice assistant available on all routes */}
      <VoiceAgent />

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard/user" element={<UserDashboard />} />
        <Route path="/dashboard/admin" element={<AdminDashboard />} />
        <Route path="/dashboard/warehouse" element={<WarehouseDashboard />} />
        <Route path="/dashboard/pharmacist" element={<PharmacistDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;