import React from 'react';
import { Outlet, NavLink, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Upload, Briefcase, Clock, LogOut } from 'lucide-react';

export default function Layout() {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload', path: '/upload', icon: Upload },
    { name: 'Jobs', path: '/jobs', icon: Briefcase },
    { name: 'History', path: '/history', icon: Clock },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside className="app-sidebar" style={{
        width: '240px',
        background: 'var(--surface-raised)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px'
      }}>
        {/* Brand */}
        <div className="brand-header" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 32px 8px' }}>
          <div style={{
            background: 'var(--accent)',
            color: 'var(--bg)',
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            fontFamily: 'var(--font-display)',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px'
          }}>
            RS
          </div>
          <span style={{ 
            fontFamily: 'var(--font-display)', 
            fontSize: '1.25rem', 
            fontWeight: '400',
            color: '#fff'
          }}>
            ResumeSense
          </span>
        </div>

        {/* Navigation */}
        <nav className="nav-menu" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: '8px',
                color: isActive ? 'var(--bg)' : 'var(--text-muted)',
                background: isActive ? 'var(--accent)' : 'transparent',
                fontWeight: isActive ? '500' : '400',
                transition: 'all 0.2s ease',
              })}
            >
              <link.icon size={18} />
              {link.name}
            </NavLink>
          ))}
        </nav>

        {/* User Card */}
        <div className="user-card" style={{
          marginTop: 'auto',
          padding: '16px 12px',
          background: 'var(--surface)',
          borderRadius: '12px',
          border: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text)', wordBreak: 'break-all' }}>
            {user?.email}
          </div>
          <button 
            onClick={logout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px',
              width: '100%',
              background: 'transparent',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              borderRadius: '6px',
            }}
            onMouseOver={e => { e.currentTarget.style.color = 'var(--red)'; e.currentTarget.style.background = 'rgba(248, 113, 113, 0.1)'; }}
            onMouseOut={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent'; }}
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{
        flex: 1,
        overflowY: 'auto',
        position: 'relative',
        background: 'var(--bg)',
      }}>
        {/* Subtle top gradient for depth */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, height: '200px',
          background: 'radial-gradient(circle at 50% -50%, rgba(200, 241, 53, 0.03), transparent)',
          pointerEvents: 'none',
          zIndex: 0
        }} />
        
        <div style={{ padding: '40px', position: 'relative', zIndex: 1, maxWidth: '1200px', margin: '0 auto' }}>
          <Outlet />
        </div>
      </main>
      
      <style dangerouslySetInnerHTML={{__html: '@media (max-width: 768px) { div[style*="display: flex; height: 100vh"] { flex-direction: column !important; } .app-sidebar { width: 100% !important; height: 60px !important; padding: 0 !important; flex-direction: row !important; border-right: none !important; border-top: 1px solid var(--border) !important; order: 2; background: var(--surface) !important; z-index: 1000; } .brand-header, .user-card { display: none !important; } .nav-menu { flex-direction: row !important; width: 100%; justify-content: space-around; align-items: center; padding: 0 8px !important; } .nav-item { padding: 8px !important; flex-direction: column !important; gap: 4px !important; font-size: 0.65rem !important; background: transparent !important; color: var(--text-muted) !important; } .nav-item.active { color: var(--accent) !important; } .nav-item svg { margin: 0 auto; } main { order: 1; height: calc(100vh - 60px) !important; } main > div:nth-child(2) { padding: 16px !important; } }'}} />
    </div>
  );
}
