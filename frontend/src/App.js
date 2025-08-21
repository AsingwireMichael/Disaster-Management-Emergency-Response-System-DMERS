import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import Responders from './pages/Responders';
import Shelters from './pages/Shelters';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="incidents" element={<Incidents />} />
              <Route path="responders" element={<Responders />} />
              <Route path="shelters" element={<Shelters />} />
              <Route path="analytics" element={<Analytics />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
