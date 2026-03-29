import React from 'react';
import { ArrowRight, XCircle, CheckCircle2, Sparkles } from 'lucide-react';

export default function BulletComparison({ originalBullets = [], rewrittenBullets = [] }) {
  if (!originalBullets.length || !rewrittenBullets.length) return null;

  return (
    <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem' }}>
        <Sparkles color="var(--amber)" size={24} />
        <h2 style={{ fontSize: '1.5rem', margin: 0, color: '#fff' }}>AI Bullet Rewrites</h2>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem', lineHeight: '1.5' }}>
        We detected weak or passive verbs in some of your bullet points. Here is how you can rewrite them to significantly improve your ATS hit rate.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {originalBullets.map((orig, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Original Card */}
            <div style={{
              background: 'rgba(244, 63, 94, 0.05)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              borderRadius: '12px',
              padding: '1.25rem',
              flex: 1
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--red)' }}>
                <XCircle size={16} />
                <span style={{ fontSize: '0.8rem', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Original</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.95rem', color: 'rgba(255,255,255,0.8)', lineHeight: '1.5' }}>{orig}</p>
            </div>
            
            {/* Arrow Divider (mobile view uses arrow down implicitly by stack) */}
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <ArrowRight size={24} style={{ transform: 'rotate(90deg)' }} className="md-rotate-0" />
            </div>

            {/* Upgraded Card */}
            <div style={{
              background: 'rgba(16, 185, 129, 0.05)',
              border: '1px solid var(--accent)',
              boxShadow: '0 0 20px rgba(16, 185, 129, 0.05)',
              borderRadius: '12px',
              padding: '1.25rem',
              flex: 1
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--accent)' }}>
                <CheckCircle2 size={16} />
                <span style={{ fontSize: '0.8rem', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Upgraded</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: '500', color: '#fff', lineHeight: '1.5' }}>{rewrittenBullets[i]}</p>
            </div>
          </div>
        ))}
      </div>
      {/* Quick injected style for md-rotate-0 which aligns the arrow horizontally on desktop */}
      <style dangerouslySetInnerHTML={{ __html: '@media (min-width: 768px) { .md-rotate-0 { transform: rotate(0deg) !important; } }' }} />
    </div>
  );
}
