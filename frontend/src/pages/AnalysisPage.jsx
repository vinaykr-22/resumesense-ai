import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Search, 
  Sparkles, 
  ChevronLeft, 
  Send, 
  Loader2, 
  AlertCircle
} from 'lucide-react';
import analysisService from '../services/analysisService';
import ATSScore from '../components/Analysis/ATSScore';
import BulletComparison from '../components/Analysis/BulletComparison';
import LearningPath from '../components/Analysis/LearningPath';

export default function AnalysisPage() {
  const { id: resumeId } = useParams();
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Load initial results if they exist
  useEffect(() => {
    async function loadResults() {
      try {
        const data = await analysisService.getV2Results(resumeId);
        if (data.status === 'completed' && data.result?.analysis_data) {
          setResults(data.result.analysis_data);
        }
      } catch (err) {
        console.error("No initial results found", err);
      }
    }
    loadResults();
  }, [resumeId]);

  const handleAnalyze = async () => {
    if (!jdText.trim()) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await analysisService.analyzeWithJD(resumeId, jdText);
      console.log('V2 Analysis Response:', JSON.stringify(response.data, null, 2));
      if (response.data) {
        setResults(response.data);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Your session for this resume has expired. Please upload it again from the dashboard.");
      } else {
        setError(err.response?.data?.detail || "Analysis failed. Please check your backend logs.");
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ paddingBottom: '4rem' }}>
      {/* Breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        <Link to="/history" style={{ transition: 'color 0.2s', ':hover': { color: '#fff' } }}>History</Link>
        <ChevronLeft size={16} />
        <span style={{ color: '#fff' }}>Advanced Analysis</span>
      </div>

      <style dangerouslySetInnerHTML={{ __html: '@media (max-width: 900px) { .v2-grid { grid-template-columns: 1fr !important; } .v2-sidebar { border-right: none !important; padding-right: 0 !important; } }' }} />
      <div className="v2-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 2fr)', gap: '2rem', alignItems: 'start' }}>
        
        {/* Left Input Sidebar */}
        <div className="v2-sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', borderRight: '1px solid var(--border)', paddingRight: '2rem' }}>
          <div>
            <h1 style={{ fontSize: '2rem', margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '12px', color: '#fff' }}>
              <Sparkles color="var(--accent)" size={28} />
              V2 Analysis
            </h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
              Compare your resume against a specific job description to find gaps and get AI improvements.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
                  Job Description Text
                </label>
                <textarea
                  style={{
                    width: '100%',
                    height: '250px',
                    background: 'var(--bg)',
                    border: '1px solid var(--border-bright)',
                    color: '#fff',
                    padding: '16px',
                    borderRadius: '12px',
                    fontSize: '0.95rem',
                    outline: 'none',
                    resize: 'none',
                    lineHeight: '1.5'
                  }}
                  placeholder="Paste the full job description here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-bright)'}
                />
              </div>

              <button
                onClick={handleAnalyze}
                disabled={loading || !jdText.trim()}
                style={{
                  width: '100%',
                  padding: '14px 24px',
                  background: loading || !jdText.trim() ? 'var(--surface)' : 'var(--accent)',
                  color: loading || !jdText.trim() ? 'var(--text-muted)' : 'var(--bg)',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: loading || !jdText.trim() ? 'not-allowed' : 'pointer',
                  transition: 'opacity 0.2s',
                  opacity: loading ? 0.8 : 1
                }}
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                {loading ? 'Analyzing Pipeline...' : 'Run Analysis'}
              </button>
            </div>
          </div>
          
          {/* Skill Mastery Roadmaps */}
          {results && !loading && (
            <div className="animate-fade-in" style={{ marginTop: '2rem' }}>
              <LearningPath data={results.learning_path} />
            </div>
          )}
        </div>

        {/* Right Results Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {error && (
            <div style={{ background: 'rgba(248, 113, 113, 0.1)', border: '1px solid var(--red)', padding: '1rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--red)' }}>
              <AlertCircle size={20} />
              <p style={{ margin: 0, fontSize: '0.9rem', fontWeight: '500' }}>{error}</p>
            </div>
          )}

          {!results && !loading && (
            <div style={{ background: 'var(--surface)', border: '2px dashed var(--border-bright)', borderRadius: '16px', padding: '4rem 2rem', textAlign: 'center' }}>
              <div style={{ width: '64px', height: '64px', margin: '0 auto 1.5rem', background: 'var(--bg)', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                <Search size={32} />
              </div>
              <h3 style={{ fontSize: '1.25rem', margin: '0 0 0.5rem 0', color: '#fff' }}>Ready for V2 Inspection</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '300px', margin: '0 auto' }}>
                Paste a job description on the left to unlock ATS scores, bullet rewrites, and custom learning paths.
              </p>
            </div>
          )}

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <div style={{ height: '300px', background: 'var(--surface)', borderRadius: '16px' }} className="animate-pulse" />
              <div style={{ height: '400px', background: 'var(--surface)', borderRadius: '16px' }} className="animate-pulse" />
            </div>
          )}

          {results && !loading && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <ATSScore 
                score={results.ats_score} 
                breakdown={results.ats_breakdown} 
              />
              
              <BulletComparison 
                originalBullets={results.weak_bullets} 
                rewrittenBullets={results.rewritten_bullets} 
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
