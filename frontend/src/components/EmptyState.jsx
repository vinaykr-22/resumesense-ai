import React from 'react';
import { Link } from 'react-router-dom';

export default function EmptyState({ 
  icon: Icon, 
  title, 
  subtitle, 
  actionLabel, 
  actionTo 
}) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '4rem 2rem',
      background: 'var(--surface)',
      borderRadius: '16px',
      border: '1px dashed var(--border-bright)',
      textAlign: 'center',
      minHeight: '300px'
    }}>
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        background: 'rgba(255,255,255,0.03)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1.5rem',
        color: 'var(--text-muted)'
      }}>
        {Icon && <Icon size={32} />}
      </div>
      
      <h3 style={{
        fontSize: '1.25rem',
        color: '#fff',
        marginBottom: '0.5rem',
        fontFamily: 'var(--font-display)'
      }}>
        {title}
      </h3>
      
      <p style={{
        color: 'var(--text-muted)',
        maxWidth: '400px',
        marginBottom: '2rem',
        lineHeight: '1.6'
      }}>
        {subtitle}
      </p>
      
      {actionLabel && actionTo && (
        <Link 
          to={actionTo}
          className="btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
