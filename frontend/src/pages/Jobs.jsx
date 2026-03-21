import React, { useState, useEffect, useMemo } from 'react';
import { Search, Briefcase, MapPin, ChevronDown, Filter, Loader2 } from 'lucide-react';
import api from '../lib/api';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'backend', label: 'Backend' },
  { value: 'frontend', label: 'Frontend' },
  { value: 'fullstack', label: 'Full Stack' },
  { value: 'data', label: 'Data & AI' },
  { value: 'devops', label: 'DevOps & Cloud' },
  { value: 'mobile', label: 'Mobile' },
];

const LEVELS = [
  { value: '', label: 'All Levels' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid Level' },
  { value: 'senior', label: 'Senior' },
];

const levelColors = {
  junior: { bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.25)', text: '#38bdf8' },
  mid: { bg: 'rgba(200, 241, 53, 0.1)', border: 'rgba(200, 241, 53, 0.25)', text: 'var(--accent)' },
  senior: { bg: 'rgba(168, 85, 247, 0.1)', border: 'rgba(168, 85, 247, 0.25)', text: '#a855f7' },
};

const categoryIcons = {
  backend: '⚙️',
  frontend: '🎨',
  fullstack: '🔗',
  data: '📊',
  devops: '☁️',
  mobile: '📱',
};

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');

  useEffect(() => {
    async function fetchJobs() {
      try {
        setLoading(true);
        const res = await api.get('/jobs/list?limit=50');
        setJobs(res.data.jobs || []);
      } catch (err) {
        console.error('Failed to load jobs:', err);
        setError('Failed to load jobs. Please try again.');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, []);

  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      const matchesSearch = !searchQuery ||
        job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.required_skills?.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesCategory = !categoryFilter || job.category === categoryFilter;
      const matchesLevel = !levelFilter || job.level === levelFilter;
      return matchesSearch && matchesCategory && matchesLevel;
    });
  }, [jobs, searchQuery, categoryFilter, levelFilter]);

  const selectStyle = {
    appearance: 'none',
    background: 'var(--surface)',
    border: '1px solid var(--border-bright)',
    color: '#fff',
    padding: '10px 36px 10px 14px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    outline: 'none',
    cursor: 'pointer',
    position: 'relative',
  };

  if (loading) {
    return (
      <div className="animate-fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh' }}>
        <Loader2 size={40} className="animate-spin" color="var(--accent)" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ paddingBottom: '4rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem 0', lineHeight: 1 }}>
          <Briefcase size={28} color="var(--accent)" style={{ display: 'inline', marginRight: '12px', verticalAlign: 'middle' }} />
          Job Board
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
          Explore {jobs.length} curated positions across tech
        </p>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex', gap: '12px', marginBottom: '2rem', flexWrap: 'wrap', alignItems: 'center',
        background: 'var(--surface)', padding: '1rem 1.5rem', borderRadius: '12px', border: '1px solid var(--border)'
      }}>
        <div style={{ position: 'relative', flex: '1 1 250px' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search jobs, skills..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg)',
              border: '1px solid var(--border-bright)',
              color: '#fff',
              padding: '10px 14px 10px 40px',
              borderRadius: '8px',
              fontSize: '0.95rem',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ position: 'relative' }}>
          <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} style={selectStyle}>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <ChevronDown size={16} color="var(--text-muted)" style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
        </div>

        <div style={{ position: 'relative' }}>
          <select value={levelFilter} onChange={e => setLevelFilter(e.target.value)} style={selectStyle}>
            {LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
          <ChevronDown size={16} color="var(--text-muted)" style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filteredJobs.length} result{filteredJobs.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--red)' }}>
          <p>{error}</p>
        </div>
      )}

      {/* Jobs Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '1rem' }}>
        {filteredJobs.map((job, idx) => {
          const lc = levelColors[job.level] || levelColors.mid;
          const icon = categoryIcons[job.category] || '💼';

          return (
            <div
              key={job.id}
              className="animate-fade-in"
              style={{
                animationDelay: `${idx * 40}ms`,
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '16px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                transition: 'border-color 0.2s, transform 0.2s',
                cursor: 'default',
              }}
              onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
              onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'translateY(0)'; }}
            >
              {/* Top row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
                    {icon} {job.title}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    <span style={{ textTransform: 'capitalize' }}>{job.category}</span>
                    <span>·</span>
                    <span style={{ textTransform: 'capitalize' }}>{job.company_type}</span>
                  </div>
                </div>

                <span style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  textTransform: 'uppercase',
                  fontWeight: '600',
                  background: lc.bg,
                  border: `1px solid ${lc.border}`,
                  color: lc.text,
                  whiteSpace: 'nowrap',
                }}>
                  {job.level}
                </span>
              </div>

              {/* Description */}
              <p style={{
                color: 'var(--text)',
                fontSize: '0.9rem',
                lineHeight: 1.5,
                margin: 0,
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}>
                {job.description}
              </p>

              {/* Required Skills */}
              <div>
                <div style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Required Skills
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {job.required_skills?.map((skill, i) => (
                    <span key={i} style={{
                      padding: '4px 10px',
                      background: 'var(--bg)',
                      border: '1px solid var(--border-bright)',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text)',
                    }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Nice to have */}
              {job.nice_to_have?.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                    Nice to Have
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {job.nice_to_have.map((skill, i) => (
                      <span key={i} style={{
                        padding: '4px 10px',
                        background: 'transparent',
                        border: '1px dashed var(--border)',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-muted)',
                      }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredJobs.length === 0 && !loading && !error && (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-muted)' }}>
          <Filter size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
          <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#fff' }}>No jobs match your filters</h3>
          <p>Try adjusting your search or filter criteria.</p>
        </div>
      )}
    </div>
  );
}
