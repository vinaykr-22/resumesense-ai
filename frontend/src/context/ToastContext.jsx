import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

let toastCount = 0;

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info') => {
    const id = ++toastCount;
    setToasts((prev) => {
      const newToasts = [...prev, { id, message, type }];
      if (newToasts.length > 3) return newToasts.slice(newToasts.length - 3);
      return newToasts;
    });

    // Auto dismiss after 4 seconds
    setTimeout(() => {
      removeToast(id);
    }, 4000);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Container */}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        zIndex: 9999,
        pointerEvents: 'none'
      }}>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

const ToastItem = ({ toast, onClose }) => {
  const [isLeaving, setIsLeaving] = useState(false);

  // Define styling map based on type
  const typeStyles = {
    success: { icon: CheckCircle, color: 'var(--accent)', bg: 'rgba(200, 241, 53, 0.1)', border: 'rgba(200, 241, 53, 0.3)' },
    error: { icon: AlertCircle, color: 'var(--red)', bg: 'rgba(248, 113, 113, 0.1)', border: 'rgba(248, 113, 113, 0.3)' },
    warning: { icon: AlertTriangle, color: 'var(--amber)', bg: 'rgba(245, 158, 11, 0.1)', border: 'rgba(245, 158, 11, 0.3)' },
    info: { icon: Info, color: 'var(--teal)', bg: 'rgba(45, 212, 191, 0.1)', border: 'rgba(45, 212, 191, 0.3)' }
  };

  const styleConfig = typeStyles[toast.type] || typeStyles.info;
  const Icon = styleConfig.icon;

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(onClose, 300); // Wait for exit animation
  };

  return (
    <div
      style={{
        background: 'var(--surface-raised)',
        border: '1px solid ' + styleConfig.border,
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        width: '320px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        pointerEvents: 'auto',
        animation: isLeaving 
          ? 'toast-slide-out 0.3s ease forwards' 
          : 'toast-slide-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}
    >
      <div style={{ color: styleConfig.color, marginTop: '2px', background: styleConfig.bg, borderRadius: '50%', padding: '4px', display: 'flex' }}>
        <Icon size={18} />
      </div>
      <div style={{ flex: 1, paddingTop: '1px' }}>
        <p style={{ margin: 0, color: '#fff', fontSize: '0.9rem', lineHeight: '1.4' }}>
          {toast.message}
        </p>
      </div>
      <button 
        onClick={handleClose}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          padding: '4px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          borderRadius: '4px',
          transition: 'background 0.2s, color 0.2s'
        }}
        onMouseOver={e => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
            e.currentTarget.style.color = '#fff';
        }}
        onMouseOut={e => {
            e.currentTarget.style.background = 'none';
            e.currentTarget.style.color = 'var(--text-muted)';
        }}
      >
        <X size={16} />
      </button>

      {/* Inject animation keyframes globally just for toasts */}
      <style>{'@keyframes toast-slide-in { 0% { transform: translateX(120%); opacity: 0; } 100% { transform: translateX(0); opacity: 1; } } @keyframes toast-slide-out { 0% { transform: translateX(0); opacity: 1; } 100% { transform: translateX(120%); opacity: 0; } }'}</style>
    </div>
  );
};
