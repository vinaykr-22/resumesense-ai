import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, FileText, CheckCircle2, ChevronDown, ChevronUp, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../lib/api';
import { SkeletonText, SkeletonCard } from '../components/Skeleton';

export default function Results() {
  const { id: resumeId } = useParams();
  
  // Data states
  const [skillsData, setSkillsData] = useState(null);
  const [jobMatches, setJobMatches] = useState([]);
  const [selectedRole, setSelectedRole] = useState('');
  
  const [gapData, setGapData] = useState(null);
  const [gapLoading, setGapLoading] = useState(false);
  
  const [suggestionsData, setSuggestionsData] = useState(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize data
  useEffect(() => {
    async function fetchInitialData() {
      try {
        setInitialLoading(true);
        // Fetch skills
        const skillsRes = await api.post('/resume/skills', { resume_id: resumeId });
        setSkillsData(skillsRes.data);
        
        // Fetch matches
        const matchRes = await api.post('/jobs/match', { resume_id: resumeId, top_k: 5 });
        const matches = matchRes.data.matches || [];
        setJobMatches(matches);
        
        if (matches.length > 0) {
          setSelectedRole(matches[0].title);
        } else {
          setSelectedRole('');
          setGapData(null);
          setSuggestionsData(null);
        }
      } catch (err) {
        setError('Failed to load analysis results. Please try again.');
        console.error(err);
      } finally {
        setInitialLoading(false);
      }
    }
    
    if (resumeId) {
      fetchInitialData();
    }
  }, [resumeId]);

  // Fetch gap & suggestions when role changes
  useEffect(() => {
    async function fetchRoleSpecificData() {
      if (!selectedRole || !resumeId) return;
      
      try {
        setGapLoading(true);
        setSuggestionsLoading(true);
        
        // Parallel requests
        const [gapRes, sugRes] = await Promise.all([
          api.post('/jobs/skill-gap', { resume_id: resumeId, job_role: selectedRole }),
          api.post('/resume/suggestions', { resume_id: resumeId, target_role: selectedRole }).catch(e => {
            console.error(e);
            return { data: null }; // Fallback if LLM fails
          })
        ]);
        
        setGapData(gapRes.data);
        if (sugRes.data) {
          setSuggestionsData(sugRes.data);
        }
      } catch (err) {
        console.error('Failed to fetch role data', err);
      } finally {
        setGapLoading(false);
        setSuggestionsLoading(false);
      }
    }
    
    fetchRoleSpecificData();
  }, [resumeId, selectedRole]);

  if (initialLoading) {
    return (
      <div style={{ paddingBottom: '4rem' }}>
        <div style={{ marginBottom: '2.5rem' }}>
          <SkeletonText width="150px" height="16px" style={{ marginBottom: '1.5rem' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '2rem' }}>
            <div>
              <SkeletonText width="300px" height="40px" style={{ marginBottom: '8px' }} />
              <SkeletonText width="200px" height="16px" />
            </div>
            <SkeletonText width="200px" height="80px" style={{ borderRadius: '16px' }} />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: '2rem' }}>
           <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
             <SkeletonCard style={{ height: '300px' }} />
             <SkeletonCard style={{ height: '400px' }} />
           </div>
           <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
             <SkeletonCard style={{ height: '100px' }} />
             <SkeletonCard style={{ height: '400px' }} />
           </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <AlertCircle size={48} color="var(--red)" style={{ margin: '0 auto 1rem' }} />
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--red)' }}>Oops</h2>
        <p style={{ color: 'var(--text-muted)' }}>{error}</p>
        <Link to="/upload" style={{ display: 'inline-block', marginTop: '1.5rem', color: 'var(--accent)' }}>&larr; Back to Upload</Link>
      </div>
    );
  }

  const overallScore =
    typeof suggestionsData?.overall_score === 'number'
      ? suggestionsData.overall_score
      : typeof gapData?.match_percentage === 'number'
        ? Math.round(gapData.match_percentage / 10)
        : 0;
  const scoreColor = overallScore >= 8 ? 'var(--accent)' : overallScore >= 6 ? 'var(--amber)' : 'var(--text-muted)';
  
  const renderScoreRing = (score, max, size, color) => {
    const data = [{ name: 'Score', value: score, fill: color }];
    return (
      <div style={{ position: 'relative', width: size, height: size }}>
        <RadialBarChart 
          width={size} 
          height={size} 
          innerRadius="70%" 
          outerRadius="100%" 
          data={data} 
          startAngle={90} 
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, max]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: 'var(--surface)' }} dataKey="value" cornerRadius={size/2} />
        </RadialBarChart>
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'var(--font-display)',
          fontSize: size * 0.4 + 'px',
          fontWeight: '300',
          color: '#fff'
        }}>
          {score}
        </div>
      </div>
    );
  };

  return (
    <div className="animate-fade-in" style={{ paddingBottom: '4rem' }}>
      
      {/* Top Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          <Link to="/upload" style={{ transition: 'color 0.2s', ':hover': { color: '#fff' } }}>Upload</Link>
          <ChevronRight size={16} />
          <span style={{ color: '#fff' }}>Results</span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '2rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '0.5rem' }}>
              <FileText size={24} color="var(--accent)" />
              <h1 style={{ fontSize: '2.5rem', margin: 0, lineHeight: 1 }}>Analysis Complete</h1>
            </div>
            <p style={{ color: 'var(--text-muted)' }}>Resume ID: {resumeId}</p>
            <div style={{ marginTop: '1rem' }}>
              <Link 
                to={`/analysis/${resumeId}`} 
                className="btn-v2"
                style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', 
                  color: '#fff', 
                  padding: '8px 16px', 
                  borderRadius: '12px', 
                  fontSize: '0.9rem', 
                  fontWeight: 'bold', 
                  textDecoration: 'none',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
                  transition: 'transform 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                <Sparkles size={16} />
                Try V2 Advanced Analysis
              </Link>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', background: 'var(--surface)', padding: '1rem 2rem', borderRadius: '16px', border: '1px solid var(--border)' }}>
            <div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Overall Score</p>
              <p style={{ fontSize: '1.25rem' }}>Out of 10</p>
            </div>
            {renderScoreRing(overallScore, 10, 80, scoreColor)}
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: '2rem', alignItems: 'start' }}>
        
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Skills Card */}
          <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Skills Found</h2>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '4px 12px', borderRadius: '100px', fontSize: '0.9rem', fontFamily: 'var(--font-mono)' }}>
                {skillsData?.all_skills?.length || 0} Total
              </div>
            </div>
            
            <SkillSection title="Technical Skills" skills={skillsData?.technical_skills} />
            <SkillSection title="Programming Languages" skills={skillsData?.programming_languages} />
            <SkillSection title="Frameworks & Tools" skills={skillsData?.frameworks_tools} />
            <SkillSection title="Soft Skills" skills={skillsData?.soft_skills} />
          </div>
          
          {/* Job Match Card */}
          <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', marginTop: 0 }}>Top Job Matches</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {jobMatches.map((job, idx) => {
                const isBestMatch = idx === 0;
                const score = job.match_score;
                const color = score >= 80 ? 'var(--accent)' : score >= 60 ? 'var(--amber)' : 'var(--text-muted)';
                
                return (
                  <div key={job.job_id} className="job-match-row" style={{ 
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
                    background: isBestMatch ? 'rgba(200, 241, 53, 0.03)' : 'var(--bg)',
                    border: isBestMatch ? '1px solid rgba(200, 241, 53, 0.2)' : '1px solid var(--border)',
                    padding: '1rem 1.5rem', borderRadius: '12px',
                    position: 'relative', overflow: 'hidden'
                  }}>
                    {isBestMatch && (
                      <div style={{ position: 'absolute', top: 0, left: 0, background: 'var(--accent)', color: 'var(--bg)', fontSize: '0.65rem', fontWeight: 'bold', padding: '2px 8px', borderBottomRightRadius: '8px', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
                        Best Match
                      </div>
                    )}
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '1.1rem', fontWeight: '500', color: '#fff' }}>{job.title}</span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                        {job.level} Level &middot; {job.category}
                      </span>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', color, lineHeight: 1 }}>{score}%</div>
                      </div>
                      <div style={{ width: '40px', height: '40px' }}>
                        {renderScoreRing(score, 100, 40, color)}
                      </div>
                    </div>
                  </div>
                );
              })}
              
              {jobMatches.length === 0 && (
                <p style={{ color: 'var(--text-muted)' }}>No job matches found.</p>
              )}
            </div>
            
            {/* BarChart Visualization */}
            {jobMatches.length > 0 && (
              <div style={{ marginTop: '2.5rem', height: '250px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}>Score Comparison</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={jobMatches} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis 
                      dataKey="title" 
                      tickFormatter={(val) => val.length > 15 ? val.substring(0, 15) + '...' : val}
                      stroke="var(--text-muted)"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      domain={[0, 100]} 
                      stroke="var(--text-muted)" 
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip 
                      cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{ background: 'var(--surface-raised)', border: '1px solid var(--border)', padding: '12px', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                              <p style={{ margin: 0, fontWeight: '500', color: '#fff' }}>{data.title}</p>
                              <p style={{ margin: '4px 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{data.category} &middot; {data.level}</p>
                              <p style={{ margin: 0, fontSize: '1.2rem', fontFamily: 'var(--font-mono)', color: data.match_score >= 80 ? 'var(--accent)' : data.match_score >= 60 ? 'var(--amber)' : 'var(--text-muted)' }}>{data.match_score}% Match</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="match_score" radius={[4, 4, 0, 0]} isAnimationActive={true} animationDuration={1000}>
                      {
                        jobMatches.map((entry, index) => {
                          const color = entry.match_score >= 80 ? 'var(--accent)' : entry.match_score >= 60 ? 'var(--amber)' : 'var(--text-muted)';
                          return <Cell key={'cell-' + index} fill={color} />;
                        })
                      }
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
          
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Target Role Selector */}
          <div style={{ background: 'var(--surface-raised)', borderRadius: '16px', padding: '1.5rem', border: '1px solid var(--border)' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              TARGET ROLE FOR GAP ANALYSIS
            </label>
            <div style={{ position: 'relative' }}>
              <select 
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                style={{
                  width: '100%',
                  appearance: 'none',
                  background: 'var(--bg)',
                  border: '1px solid var(--border-bright)',
                  color: '#fff',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                {jobMatches.map(j => (
                  <option key={j.job_id} value={j.title}>{j.title}</option>
                ))}
              </select>
              <ChevronDown size={20} color="var(--text-muted)" style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            </div>
          </div>

          {/* Skill Gap Card */}
          <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden' }}>
            {gapLoading && (
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(19,20,23,0.8)', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(2px)' }}>
                <Loader2 size={32} className="animate-spin" color="var(--accent)" />
              </div>
            )}
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Skill Gap</h2>
                <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Compared against required skills</p>
              </div>
              {gapData && renderScoreRing(gapData.match_percentage, 100, 60, gapData.match_percentage >= 80 ? 'var(--accent)' : gapData.match_percentage >= 50 ? 'var(--amber)' : 'var(--red)')}
            </div>

            {gapData && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {gapData.missing_skills?.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--red)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>Missing Skills</h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {gapData.missing_skills.map((skill, i) => (
                        <span key={i} style={{ padding: '6px 12px', background: 'rgba(248, 113, 113, 0.1)', color: 'var(--red)', border: '1px solid rgba(248, 113, 113, 0.2)', borderRadius: '6px', fontSize: '0.9rem' }}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {gapData.partial_matches?.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--amber)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>Partial Matches</h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {gapData.partial_matches.map((pm, i) => (
                        <span key={i} style={{ padding: '6px 12px', background: 'rgba(245, 158, 11, 0.1)', color: 'var(--amber)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '6px', fontSize: '0.9rem' }}>
                          {pm.job_skill} &approx; {pm.resume_skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {gapData.matched_skills?.length > 0 && (
                  <div>
                    <h4 style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--accent)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>Matched Skills</h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {gapData.matched_skills.map((ms, i) => (
                        <span key={i} style={{ padding: '6px 12px', background: 'rgba(200, 241, 53, 0.05)', color: 'var(--accent)', border: '1px solid rgba(200, 241, 53, 0.2)', borderRadius: '6px', fontSize: '0.9rem' }}>
                          {ms.job_skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {!gapData && !gapLoading && <p style={{ color: 'var(--text-muted)' }}>Select a role to view the gap analysis.</p>}
          </div>

          {/* AI Suggestions Card */}
          {suggestionsData && (
            <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden' }}>
              {suggestionsLoading && (
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(19,20,23,0.8)', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(2px)' }}>
                  <Loader2 size={32} className="animate-spin" color="var(--accent)" />
                </div>
              )}
              
              <h2 style={{ fontSize: '1.5rem', margin: '0 0 1rem 0' }}>AI Suggestions</h2>
              <p style={{ color: '#fff', fontSize: '1.1rem', marginBottom: '2rem', fontStyle: 'italic', borderLeft: '2px solid var(--accent)', paddingLeft: '1rem' }}>
                "{suggestionsData.summary}"
              </p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                {suggestionsData.suggestions?.map((sug, i) => (
                  <ExpandableSuggestion key={i} suggestion={sug} />
                ))}
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1.5rem' }}>
                {suggestionsData.ats_tips?.length > 0 && (
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                    <h4 style={{ fontSize: '0.9rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '1rem', textTransform: 'uppercase' }}>ATS Tips</h4>
                    <ol style={{ paddingLeft: '1.2rem', margin: 0, color: 'var(--text)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {suggestionsData.ats_tips.map((tip, i) => <li key={i}>{tip}</li>)}
                    </ol>
                  </div>
                )}
                
                {suggestionsData.strengths?.length > 0 && (
                  <div style={{ background: 'rgba(200,241,53,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(200,241,53,0.1)' }}>
                    <h4 style={{ fontSize: '0.9rem', fontFamily: 'var(--font-mono)', color: 'var(--accent)', marginBottom: '1rem', textTransform: 'uppercase' }}>Identified Strengths</h4>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {suggestionsData.strengths.map((str, i) => (
                        <li key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                          <CheckCircle2 size={16} color="var(--accent)" style={{ flexShrink: 0, marginTop: '2px' }} />
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
      
      {/* Mobile media query injected via style component approach */}
      <style dangerouslySetInnerHTML={{__html: '@media (max-width: 900px) { .animate-fade-in > div:nth-child(2) { grid-template-columns: 1fr !important; } }' }} />
    </div>
  );
}

// Helper components

function SkillSection({ title, skills }) {
  if (!skills || skills.length === 0) return null;
  
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>{title}</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {skills.map((skill, index) => (
          <span 
            key={index} 
            className="animate-fade-in skill-tag"
            style={{ 
              animationDelay: (index * 30) + 'ms',
              padding: '6px 12px', 
              background: 'var(--bg)', 
              border: '1px solid var(--border-bright)', 
              borderRadius: '6px', 
              fontSize: '0.9rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text)',
              transition: 'border-color 0.2s ease'
            }}
            onMouseOver={e => e.target.style.borderColor = 'var(--accent)'}
            onMouseOut={e => e.target.style.borderColor = 'var(--border-bright)'}
          >
            {skill}
          </span>
        ))}
      </div>
    </div>
  );
}

function ExpandableSuggestion({ suggestion }) {
  const [expanded, setExpanded] = useState(false);
  
  const priorityColors = {
    high: 'var(--red)',
    medium: 'var(--amber)',
    low: 'var(--teal)'
  };
  
  const pColor = priorityColors[suggestion.priority] || 'var(--text-muted)';
  
  return (
    <div style={{ 
      background: 'var(--bg)', 
      border: '1px solid var(--border)', 
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{ 
          padding: '1rem', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          cursor: 'pointer',
          background: expanded ? 'rgba(255,255,255,0.02)' : 'transparent'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ 
            padding: '2px 8px', 
            borderRadius: '4px', 
            fontSize: '0.7rem', 
            fontFamily: 'var(--font-mono)', 
            textTransform: 'uppercase',
            border: '1px solid ' + pColor,
            color: pColor,
            background: 'color-mix(in srgb, ' + pColor + ' 10%, transparent)'
          }}>
            {suggestion.priority}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{suggestion.category}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: '500', color: '#fff' }}>{suggestion.issue}</span>
          {expanded ? <ChevronUp size={18} color="var(--text-muted)" /> : <ChevronDown size={18} color="var(--text-muted)" />}
        </div>
      </div>
      
      {expanded && (
        <div style={{ padding: '0 1rem 1rem 1rem', borderTop: '1px solid var(--border)' }}>
          <div style={{ marginTop: '1rem', color: 'var(--text)', fontSize: '0.95rem', lineHeight: 1.6 }}>
            <strong style={{ color: '#fff', display: 'block', marginBottom: '4px' }}>How to fix:</strong>
            {suggestion.fix}
          </div>
          
          {suggestion.example && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', borderLeft: '2px solid var(--accent)' }}>
              <span style={{ display: 'block', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Example</span>
              <p style={{ margin: 0, fontSize: '0.9rem', fontFamily: 'var(--font-mono)' }}>{suggestion.example}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
