import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle2, Loader2, AlertCircle, X } from 'lucide-react';
import api from '../lib/api';

const STAGES = [
  { id: 'parsing', label: 'Parsing resume...', endProgress: 25 },
  { id: 'extraction', label: 'Extracting skills...', endProgress: 60 },
  { id: 'embedding', label: 'Generating embeddings...', endProgress: 85 },
  { id: 'matching', label: 'Matching jobs...', endProgress: 100 }
];

export default function Upload() {
  const [file, setFile] = useState(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [resumeId, setResumeId] = useState(null);
  
  // Processing state
  const [status, setStatus] = useState(null); // 'uploading', 'processing', 'completed', 'failed'
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setErrorMsg(null);
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(selectedFile.type)) {
      setErrorMsg("Please upload a PDF or DOCX file.");
      return;
    }
    
    if (selectedFile.size > 5 * 1024 * 1024) {
      setErrorMsg("File size must be under 5MB.");
      return;
    }
    
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setStatus('uploading');
    setProgress(5); // Initial simulated progress
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await api.post('/resume/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setJobId(response.data.job_id);
      setResumeId(response.data.resume_id);
      setStatus('processing');
      setProgress(10);
      
    } catch (err) {
      setStatus('failed');
      setErrorMsg(err.response?.data?.detail || "Failed to upload file. Please try again.");
    }
  };

  // Polling Effect
  useEffect(() => {
    let intervalId;
    
    if (status === 'processing' && jobId) {
      intervalId = setInterval(async () => {
        try {
          const res = await api.get(`/resume/status/${jobId}`);
          const data = res.data;
          
          if (data.status === 'completed') {
            setProgress(100);
            setStatus('completed');
            clearInterval(intervalId);
            
            // Navigate after brief delay for visual completion
            setTimeout(() => {
              navigate(`/results/${resumeId}`);
            }, 500);
            
          } else if (data.status === 'failed') {
            setStatus('failed');
            setErrorMsg(data.error || "Processing failed internally.");
            clearInterval(intervalId);
          } else {
            // Mapping backend progress cleanly to our UI display
            setProgress(data.progress || 15);
          }
        } catch (err) {
          setStatus('failed');
          setErrorMsg("Failed to check status. Server might be down.");
          clearInterval(intervalId);
        }
      }, 2000);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [status, jobId, resumeId, navigate]);


  // Calculate the active stage index based on progress
  const getActiveStageIndex = () => {
    if (progress === 0) return -1;
    for (let i = 0; i < STAGES.length; i++) {
      if (progress <= STAGES[i].endProgress) {
        return i;
      }
    }
    return STAGES.length - 1;
  };

  const activeStageIndex = getActiveStageIndex();

  const resetUpload = () => {
    setFile(null);
    setStatus(null);
    setProgress(0);
    setErrorMsg(null);
    setJobId(null);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.75rem', fontFamily: 'var(--font-display)' }}>Analyze your resume</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Get AI-powered skill matching and career insights</p>
      </div>

      {status === 'failed' && (
        <div className="animate-fade-in" style={{
          background: 'rgba(248, 113, 113, 0.05)',
          border: '1px solid var(--red)',
          borderRadius: '12px',
          padding: '24px',
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          <AlertCircle size={48} color="var(--red)" style={{ margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: '1.25rem', marginBottom: '8px', color: 'var(--red)' }}>Processing Failed</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>{errorMsg}</p>
          <button onClick={resetUpload} style={{
            background: 'var(--surface-raised)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
            padding: '10px 20px',
            borderRadius: '6px'
          }}>
            Try another file
          </button>
        </div>
      )}

      {/* Upload Zone */}
      {(!status || status === 'uploading') && !errorMsg && (
        <div style={{ position: 'relative' }} className="upload-container">
          <div
            className="upload-zone"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={() => !file && fileInputRef.current?.click()}
            style={{
              border: isDragging || isHovered ? '2px dashed var(--accent)' : '2px dashed var(--border-bright)',
              background: isDragging ? 'rgba(200, 241, 53, 0.05)' : isHovered ? 'var(--surface-raised)' : 'var(--surface)',
              borderRadius: '16px',
              padding: '4rem 2rem',
              textAlign: 'center',
              cursor: file ? 'default' : 'pointer',
              transition: 'all 0.3s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '320px'
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            />
            
            {file ? (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                <div style={{ 
                  display: 'flex', alignItems: 'center', gap: '12px', 
                  background: 'var(--bg)', padding: '12px 24px', 
                  borderRadius: '100px', border: '1px solid var(--border-bright)' 
                }}>
                  <FileText size={20} color="var(--accent)" />
                  <span style={{ fontFamily: 'var(--font-body)', fontWeight: '500' }}>{file.name}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                  {!status && (
                    <button onClick={(e) => { e.stopPropagation(); setFile(null); }} style={{ background: 'none', color: 'var(--text-muted)', marginLeft: '8px', display: 'flex' }}>
                      <X size={16} />
                    </button>
                  )}
                </div>
                
                {status === 'uploading' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent)' }}>
                    <Loader2 size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                    <span style={{ fontFamily: 'var(--font-mono)' }}>Uploading...</span>
                  </div>
                ) : (
                  <button className="primary" onClick={(e) => { e.stopPropagation(); handleUpload(); }} style={{ fontSize: '1.1rem', padding: '14px 32px' }}>
                    Analyze Resume
                  </button>
                )}
              </div>
            ) : (
              <div style={{ pointerEvents: 'none' }}>
                <div style={{ 
                  background: 'var(--bg)', width: '64px', height: '64px', 
                  borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', 
                  margin: '0 auto 1.5rem', border: '1px solid var(--border)',
                  color: (isDragging || isHovered) ? 'var(--accent)' : 'var(--text-muted)',
                  transition: 'color 0.3s ease'
                }}>
                  <UploadCloud size={32} />
                </div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: (isDragging || isHovered) ? '#fff' : 'var(--text-muted)', transition: 'color 0.3s ease' }}>
                  Drop your resume here
                </h3>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  PDF or DOCX · Max 5MB
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Processing States Card */}
      {status === 'processing' && (
        <div className="animate-fade-in" style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '16px',
          padding: '2.5rem',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
            <div>
              <h3 style={{ fontSize: '1.5rem', margin: 0 }}>Processing Document</h3>
              <p style={{ color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Our AI is extracting insights...</p>
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '3rem', fontWeight: '300', color: 'var(--accent)', lineHeight: 1 }}>
              {progress}%
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {STAGES.map((stage, index) => {
              const isActive = index === activeStageIndex;
              const isPast = index < activeStageIndex || progress === 100;
              const isPending = index > activeStageIndex && progress < 100;
              
              let stageColor = 'var(--text-muted)';
              if (isActive) stageColor = '#fff';
              if (isPast) stageColor = 'var(--accent)';

              return (
                <div key={stage.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', opacity: isPending ? 0.5 : 1, transition: 'all 0.3s ease' }}>
                  <div style={{ width: '24px', display: 'flex', justifyContent: 'center' }}>
                    {isPast ? (
                      <CheckCircle2 size={24} color="var(--accent)" />
                    ) : isActive ? (
                      <Loader2 size={24} color="var(--accent)" style={{ animation: 'spin 1s linear infinite' }} />
                    ) : (
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--border)' }} />
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: stageColor }}>{stage.label}</span>
                    </div>
                    {/* Animated Progress Bar Sub-track */}
                    <div style={{ width: '100%', background: 'var(--bg)', height: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ 
                        height: '100%', 
                        background: 'var(--accent)',
                        width: isPast ? '100%' : isActive ? (((progress - (index > 0 ? STAGES[index-1].endProgress : 0)) / (stage.endProgress - (index > 0 ? STAGES[index-1].endProgress : 0))) * 100) + '%' : '0%',
                        transition: 'width 0.5s ease-out'
                      }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
