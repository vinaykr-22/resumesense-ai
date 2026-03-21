import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import UploadPage from './pages/Upload';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Results from './pages/Results';
import Jobs from './pages/Jobs';

import { ToastProvider } from './context/ToastContext';

import { useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';

// Tiny custom router transition wrapper
const TransitionWrapper = ({ children }) => {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransitionStage] = useState('enter');

  useEffect(() => {
    if (location.pathname !== displayLocation.pathname) {
      setTransitionStage('exit');
      const timeout = setTimeout(() => {
        setDisplayLocation(location);
        setTransitionStage('enter');
      }, 200); // 200ms fade out
      return () => clearTimeout(timeout);
    }
  }, [location, displayLocation]);

  return (
    <div className={transitionStage === 'enter' ? 'page-enter' : 'page-exit'} style={{ height: '100%' }}>
      {React.cloneElement(children, { location: displayLocation })}
    </div>
  );
};

const AppRoutes = () => {
  return (
    <TransitionWrapper>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes inside Layout */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="history" element={<History />} />
          <Route path="results/:id" element={<Results />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </TransitionWrapper>
  );
};

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Router>
          <AppRoutes />
        </Router>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
