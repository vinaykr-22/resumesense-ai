import React from 'react';
import { Target, FileText, LayoutList, Type } from 'lucide-react';

export default function ATSScore({ score, breakdown }) {
  if (!breakdown) return null;

  const metrics = [
    { label: 'Keywords & Skills', value: breakdown.keyword_score, max: 40, icon: Target, color: '#3b82f6' },
    { label: 'Section Completeness', value: breakdown.section_completeness, max: 30, icon: LayoutList, color: '#8b5cf6' },
    { label: 'Bullet Strength', value: breakdown.bullet_strength, max: 20, icon: FileText, color: '#a855f7' },
    { label: 'Formatting', value: breakdown.formatting_score, max: 10, icon: Type, color: '#ec4899' },
  ];

  const getScoreColor = (s) => {
    if (s >= 80) return 'var(--accent)';
    if (s >= 60) return 'var(--amber)';
    return 'var(--red)';
  };

  return (
    <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', margin: '0 0 4px 0', color: '#fff' }}>ATS Compatibility Score</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>Based on industry-standard parsing algorithms</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: '3.5rem', fontWeight: 'bold', lineHeight: 1, fontFamily: 'var(--font-display)', color: getScoreColor(score) }}>
            {score !== undefined ? Math.round(score) : 0}
          </span>
          <span style={{ fontSize: '1.25rem', fontWeight: '500', color: 'var(--text-muted)' }}>/ 100</span>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{ __html: '@media (max-width: 768px) { .ats-grid { grid-template-columns: 1fr !important; } }' }} />
      <div className="ats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
        {metrics.map((m, i) => (
          <div key={i} style={{ background: 'var(--bg)', borderRadius: '12px', padding: '1.25rem', border: '1px solid var(--border)', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
            <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', color: m.color }}>
              <m.icon size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: '500', color: '#fff', fontSize: '0.9rem' }}>{m.label}</span>
                <span style={{ fontWeight: 'bold', color: '#fff', fontSize: '0.95rem' }}>
                  {m.value !== undefined ? Math.round(m.value) : 0} <span style={{ color: 'var(--text-muted)', fontWeight: 'normal' }}>/ {m.max}</span>
                </span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'var(--surface-raised)', borderRadius: '100px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    height: '100%', 
                    borderRadius: '100px', 
                    background: m.color,
                    transition: 'width 1s ease',
                    width: `${m.value !== undefined ? Math.min(100, (m.value / m.max) * 100) : 0}%` 
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
