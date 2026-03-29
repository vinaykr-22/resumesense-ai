import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, ArrowRight, Activity, TrendingUp, Award, Clock, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import EmptyState from '../components/EmptyState';

export default function Dashboard() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Derive greeting based on time of day
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const name = user?.email?.split('@')[0] || 'User';

  useEffect(() => {
    async function fetchDashboardData() {
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
    fetchDashboardData();
  }, []);

  // Compute dummy stats for UI (since backend history is lightweight MVP right now)
  const totalAnalyzed = history.length;
  const bestScore = totalAnalyzed > 0 ? 86 : 0; // Mock score for design
  const skillsIdentified = totalAnalyzed * 34; // Mock skills multiplier

  const StatCard = ({ label, value, icon: StatIcon, color }) => (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '16px',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute',
        top: '-10px',
        right: '-10px',
        opacity: 0.1,
        color: color
      }}>
        <StatIcon size={100} />
      </div>
      <div style={{ 
        fontFamily: 'var(--font-display)', 
        fontSize: '3rem', 
        lineHeight: 1,
        color: '#fff',
        zIndex: 1
      }}>
        {value}
      </div>
      <div style={{ 
        fontFamily: 'var(--font-mono)', 
        fontSize: '0.85rem', 
        color: 'var(--text-muted)',
        textTransform: 'uppercase',
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        <StatIcon size={14} color={color} />
        {label}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div style={{ padding: '2rem' }} className="animate-fade-in">
        <div style={{ height: '40px', width: '300px', background: 'var(--surface)', borderRadius: '8px', marginBottom: '2rem' }} className="animate-pulse" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '3rem' }}>
          {[1, 2, 3].map(i => <div key={i} style={{ height: '140px', background: 'var(--surface)', borderRadius: '16px' }} className="animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ paddingBottom: '3rem' }}>
      <h1 style={{ 
        fontSize: '2.5rem', 
        fontFamily: 'var(--font-display)', 
        marginBottom: '2rem',
        color: '#fff'
      }}>
        {greeting}, <span style={{ color: 'var(--accent)' }}>{name}</span>.
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <StatCard label="Resumes Analyzed" value={totalAnalyzed} icon={FileText} color="var(--accent)" />
        <StatCard label="Top Match Score" value={bestScore ? (bestScore + '%') : '--'} icon={Award} color="var(--amber)" />
        <StatCard label="Skills Identified" value={skillsIdentified || '--'} icon={Activity} color="var(--teal)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        
        {/* Recent Activity */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Recent Activity</h2>
            {history.length > 0 && (
              <Link to="/history" style={{ 
                fontFamily: 'var(--font-mono)', 
                fontSize: '0.85rem', 
                color: 'var(--text-muted)',
                display: 'flex', alignItems: 'center', gap: '4px',
                transition: 'color 0.2s'
              }} onMouseOver={e => e.currentTarget.style.color = '#fff'} onMouseOut={e => e.currentTarget.style.color = 'var(--text-muted)'}>
                View all <ArrowRight size={14} />
              </Link>
            )}
          </div>

          {history.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {history.slice(0, 3).map((item) => (
                <div key={item.resume_id} style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.25rem 1.5rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'border-color 0.2s ease, transform 0.2s ease',
                }}
                onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--border-bright)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'none'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                      <FileText size={20} />
                    </div>
                    <div>
                      <div style={{ color: '#fff', fontWeight: '500', marginBottom: '4px' }}>{item.filename}</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        <Clock size={12} />
                        {new Date(item.uploaded_at).toLocaleDateString()}
                        {/* {item.top_match && <><span style={{ opacity: 0.5 }}>•</span> <span>Matched: {item.top_match}</span></>} */}
                      </div>
                    </div>
                  </div>
                  
                  <Link to={'/results/' + item.resume_id} style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    fontSize: '0.9rem',
                    color: 'var(--text)',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                  onMouseOut={e => e.currentTarget.style.borderColor = 'var(--border)'}
                  >
                    View results
                  </Link>
                  <Link to={'/analysis/' + item.resume_id} style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    fontSize: '0.9rem',
                    color: '#6366f1',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontWeight: 'bold',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={e => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'; e.currentTarget.style.borderColor = '#6366f1'; }}
                  onMouseOut={e => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'; e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.3)'; }}
                  >
                    <Sparkles size={14} />
                    V2 Advanced
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState 
              icon={TrendingUp}
              title="No analyses yet"
              subtitle="Upload your first resume to see your personalized skills breakdown and job matches."
              actionLabel="Analyze Resume"
              actionTo="/upload"
            />
          )}
        </div>

        {/* CTA Banner */}
        <div style={{
          background: 'var(--accent)',
          borderRadius: '16px',
          padding: '2.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '1rem',
          boxShadow: '0 10px 40px -10px rgba(200, 241, 53, 0.3)'
        }}>
          <div>
            <h2 style={{ 
              fontFamily: 'var(--font-display)', 
              fontSize: '2rem', 
              color: 'var(--bg)',
              margin: '0 0 0.5rem 0'
            }}>
              Ready to verify another resume?
            </h2>
            <p style={{ color: 'rgba(11, 12, 14, 0.7)', margin: 0, fontSize: '1.1rem' }}>
              Drop in a fresh PDF or DOCX to run the pipeline again.
            </p>
          </div>
          
          <Link to="/upload" style={{
            background: 'var(--bg)',
            color: '#fff',
            padding: '12px 24px',
            borderRadius: '100px',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'transform 0.2s'
          }}
          onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseOut={e => e.currentTarget.style.transform = 'none'}
          >
            Go to Upload <ArrowRight size={18} />
          </Link>
        </div>
        
      </div>
    </div>
  );
}
