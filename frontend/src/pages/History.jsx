import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Clock, PackageOpen, Award, ChevronRight } from 'lucide-react';
import api from '../lib/api';
import EmptyState from '../components/EmptyState';
import { SkeletonHistoryRow } from '../components/Skeleton';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await api.get('/resume/history');
        if (res.data && Array.isArray(res.data)) {
          setHistory(res.data);
        }
      } catch (error) {
        console.error('Failed to fetch history', error);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  // Helper for relative time (mocking simple values for MVP, or just using Date)
  const getRelativeTime = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return diffDays + ' days ago';
    if (diffDays < 30) return Math.floor(diffDays / 7) + ' weeks ago';
    return date.toLocaleDateString();
  };


  return (
    <div className="animate-fade-in" style={{ paddingBottom: '4rem' }}>
      <h1 style={{ 
        fontSize: '2.5rem', 
        fontFamily: 'var(--font-display)', 
        marginBottom: '2.5rem',
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <Clock size={32} color="var(--accent)" />
        Analysis History
      </h1>

      {loading ? (
        <div>
          {[1, 2, 3, 4, 5].map(i => <SkeletonHistoryRow key={i} />)}
        </div>
      ) : history.length === 0 ? (
        <EmptyState 
          icon={PackageOpen}
          title="No analyses yet"
          subtitle="It looks like you haven't uploaded any resumes yet. Start your first analysis to see it tracked here."
          actionLabel="Upload Resume"
          actionTo="/upload"
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Header Row */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'minmax(200px, 2fr) 1fr 1fr 1fr 100px', 
            padding: '0 1.5rem 0.75rem', 
            fontSize: '0.85rem', 
            textTransform: 'uppercase', 
            fontFamily: 'var(--font-mono)', 
            color: 'var(--text-muted)' 
          }}>
            <div>Document</div>
            <div>Uploaded</div>
            <div>Top Match</div>
            <div>Score</div>
            <div style={{ textAlign: 'right' }}>Action</div>
          </div>

          {/* Data Rows */}
          {history.map((item) => {
            // Mocking derived data since history API currently returns lightweight payload
            const mockScore = Math.floor(Math.random() * 30) + 65; // Random 65-94
            const mockRole = ['Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer'][Math.floor(Math.random() * 4)];
            
            const scoreColor = mockScore >= 80 ? 'var(--accent)' : mockScore >= 70 ? 'var(--amber)' : 'var(--text-muted)';
            const scoreBg = mockScore >= 80 ? 'rgba(200, 241, 53, 0.1)' : mockScore >= 70 ? 'rgba(245, 158, 11, 0.1)' : 'rgba(255,255,255,0.05)';

            return (
              <div key={item.resume_id} style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '1.25rem 1.5rem',
                display: 'grid',
                gridTemplateColumns: 'minmax(200px, 2fr) 1fr 1fr 1fr 100px',
                alignItems: 'center',
                transition: 'all 0.2s ease',
              }}
              className="history-row"
              >
                {/* Column 1: Document */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingRight: '1rem' }}>
                  <div style={{ 
                    width: '40px', 
                    height: '40px', 
                    flexShrink: 0,
                    borderRadius: '8px', 
                    background: 'var(--surface-raised)', 
                    border: '1px solid var(--border-bright)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', 
                    color: 'var(--text)' 
                  }}>
                    <FileText size={20} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ color: '#fff', fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.filename}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      ID: {item.resume_id.replace('res_', '').substring(0, 8)}...
                    </div>
                  </div>
                </div>

                {/* Column 2: Uploaded */}
                <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  {getRelativeTime(item.uploaded_at)}
                </div>

                {/* Column 3: Top Match (Mocked) */}
                <div style={{ fontSize: '0.9rem', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '1rem' }}>
                  {mockRole}
                </div>

                {/* Column 4: Score (Mocked) */}
                <div>
                  <div style={{ 
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    padding: '4px 10px', borderRadius: '100px',
                    background: scoreBg, color: scoreColor,
                    fontSize: '0.85rem', fontWeight: '600', fontFamily: 'var(--font-mono)'
                  }}>
                    {mockScore >= 80 && <Award size={14} />}
                    {mockScore}%
                  </div>
                </div>

                {/* Column 5: Action */}
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Link to={'/results/' + item.resume_id} style={{
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    background: 'var(--surface-raised)',
                    border: '1px solid var(--border-bright)',
                    fontSize: '0.9rem',
                    color: '#fff',
                    transition: 'all 0.2s',
                    textDecoration: 'none'
                  }}
                  onMouseOver={e => {
                    e.currentTarget.style.borderColor = 'var(--accent)';
                    e.currentTarget.style.color = 'var(--accent)';
                  }}
                  onMouseOut={e => {
                    e.currentTarget.style.borderColor = 'var(--border-bright)';
                    e.currentTarget.style.color = '#fff';
                  }}
                  >
                    View
                  </Link>
                </div>

              </div>
            );
          })}
        </div>
      )}

      <style dangerouslySetInnerHTML={{__html: '@media (max-width: 900px) { .history-row, .history-row + div { display: flex !important; flex-direction: column; align-items: flex-start !important; gap: 1rem; } .history-row > div:nth-child(n+2) { padding-left: 3.5rem; } .history-row > div:last-child { width: 100%; justify-content: flex-start !important; margin-top: 0.5rem; } .history-row > div { width: 100%; } }' }} />
    </div>
  );
}
