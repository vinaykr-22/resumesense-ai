import React from 'react';

// Global shimmer animation styles injected once
const ShimmerStyles = () => (
  <style dangerouslySetInnerHTML={{__html: "@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } } .skeleton-base { background: var(--surface-raised); position: relative; overflow: hidden; } .skeleton-base::after { content: ''; position: absolute; top: 0; right: 0; bottom: 0; left: 0; transform: translateX(-100%); background-image: linear-gradient(90deg, rgba(255, 255, 255, 0) 0, rgba(255, 255, 255, 0.05) 20%, rgba(255, 255, 255, 0.1) 60%, rgba(255, 255, 255, 0)); animation: shimmer 1.5s infinite; }" }} />
);

export const SkeletonText = ({ width = '100%', height = '20px', className = '', style = {} }) => (
  <>
    <ShimmerStyles />
    <div 
      className={'skeleton-base ' + className} 
      style={{ width, height, borderRadius: '4px', ...style }} 
    />
  </>
);

export const SkeletonCard = ({ className = '', style = {} }) => (
  <>
    <ShimmerStyles />
    <div 
      className={'skeleton-base ' + className} 
      style={{ 
        width: '100%', 
        height: '200px', 
        borderRadius: '16px',
        border: '1px solid var(--border)',
        ...style 
      }} 
    />
  </>
);

export const SkeletonJobRow = () => (
  <>
    <ShimmerStyles />
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1rem',
      borderBottom: '1px solid var(--border)'
    }}>
      <div style={{ width: '60%' }}>
        <SkeletonText width="70%" height="24px" style={{ marginBottom: '8px' }} />
        <SkeletonText width="40%" height="16px" />
      </div>
      <div style={{ width: '80px' }}>
         <SkeletonText width="100%" height="32px" style={{ borderRadius: '16px' }} />
      </div>
    </div>
  </>
);

export const SkeletonHistoryRow = () => (
  <>
    <ShimmerStyles />
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: '12px',
      padding: '1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: '1rem',
      position: 'relative',
      overflow: 'hidden'
    }} className="skeleton-base">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '40%', position: 'relative', zIndex: 1 }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          <div style={{ height: '16px', width: '80%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }} />
          <div style={{ height: '12px', width: '40%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }} />
        </div>
      </div>
      <div style={{ width: '20%', height: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', position: 'relative', zIndex: 1 }} />
      <div style={{ width: '10%', height: '28px', background: 'rgba(255,255,255,0.05)', borderRadius: '14px', position: 'relative', zIndex: 1 }} />
      <div style={{ width: '100px', height: '36px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', position: 'relative', zIndex: 1 }} />
    </div>
  </>
);
