import React from 'react';
import { BookOpen, ExternalLink, Award, PlayCircle, Map } from 'lucide-react';

export default function LearningPath({ data }) {
  if (!data || !data.skill_roadmaps?.length) return null;

  const { skill_roadmaps = [] } = data;

  const CourseCard = ({ course }) => (
    <a 
      href={course.url} 
      target="_blank" 
      rel="noopener noreferrer"
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '1.25rem',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        background: 'rgba(255,255,255,0.02)',
        textDecoration: 'none',
        transition: 'background 0.2s, border-color 0.2s'
      }}
      onMouseOver={e => { e.currentTarget.style.borderColor = '#8b5cf6'; e.currentTarget.style.background = 'rgba(139, 92, 246, 0.05)' }}
      onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'rgba(255,255,255,0.02)' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#8b5cf6', background: 'rgba(139, 92, 246, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
          {course.provider}
        </span>
        <ExternalLink size={14} color="var(--text-muted)" />
      </div>
      <h4 style={{ margin: '0 0 8px 0', fontSize: '0.95rem', color: '#fff', fontWeight: '600', lineHeight: 1.4 }}>
        {course.title}
      </h4>
      {course.duration_hours && (
        <div style={{ marginTop: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <BookOpen size={12} />
          ~{course.duration_hours} hours
        </div>
      )}
      <div style={{
        marginTop: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        color: '#8b5cf6',
        fontSize: '0.85rem',
        fontWeight: '600',
        textDecoration: 'underline'
      }}>
        View Full Course <ExternalLink size={14} />
      </div>
    </a>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
      <style dangerouslySetInnerHTML={{ __html: '@media (max-width: 768px) { .course-grid { grid-template-columns: 1fr !important; } }' }} />
      
      {skill_roadmaps.map((roadmap, idx) => (
        <div key={idx} style={{ background: 'var(--surface)', borderRadius: '16px', padding: '2rem', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
            <Map color="#3b82f6" size={24} />
            <h2 style={{ fontSize: '1.5rem', margin: 0, color: '#fff' }}>
              Mastery Roadmap: <span style={{ color: '#3b82f6' }}>{roadmap.skill}</span>
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
            
            {/* Beginner Tier */}
            {roadmap.beginner?.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem' }}>1</div>
                  Step 1: The Basics
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem', marginLeft: '36px' }}>Foundational concepts and introductory syntax.</p>
                <div className="course-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginLeft: '36px' }}>
                  {roadmap.beginner.map((c, i) => <CourseCard key={i} course={c} />)}
                </div>
              </div>
            )}

            {/* Intermediate Tier */}
            {roadmap.intermediate?.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(139, 92, 246, 0.2)', color: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem' }}>2</div>
                  Step 2: Gaining Proficiency
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem', marginLeft: '36px' }}>Advanced concepts, frameworks, and practical projects.</p>
                <div className="course-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginLeft: '36px' }}>
                  {roadmap.intermediate.map((c, i) => <CourseCard key={i} course={c} />)}
                </div>
              </div>
            )}

            {/* Advanced Tier */}
            {roadmap.advanced?.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem' }}>3</div>
                  Step 3: Final Mastery
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem', marginLeft: '36px' }}>Architectural design, performance tuning, and deep dives.</p>
                <div className="course-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginLeft: '36px' }}>
                  {roadmap.advanced.map((c, i) => <CourseCard key={i} course={c} />)}
                </div>
              </div>
            )}

            {/* Certifications */}
            {roadmap.certifications?.length > 0 && (
              <div style={{ marginTop: '1rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'rgba(255,255,255,0.9)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Award size={16} color="var(--amber)" />
                  Target Certifications
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {roadmap.certifications.map((cert, i) => (
                    <a 
                      key={i} 
                      href={cert.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px', 
                        padding: '8px 16px', 
                        background: 'rgba(245, 158, 11, 0.1)', 
                        border: '1px solid rgba(245, 158, 11, 0.3)', 
                        borderRadius: '8px', 
                        color: 'var(--amber)', 
                        fontSize: '0.85rem', 
                        fontWeight: '600',
                        textDecoration: 'none',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={e => e.currentTarget.style.background = 'rgba(245, 158, 11, 0.2)'}
                      onMouseOut={e => e.currentTarget.style.background = 'rgba(245, 158, 11, 0.1)'}
                    >
                      <Award size={14} />
                      {cert.name} <ExternalLink size={12} style={{ marginLeft: '4px' }} />
                    </a>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      ))}
    </div>
  );
}
