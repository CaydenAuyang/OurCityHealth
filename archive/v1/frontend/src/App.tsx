import React, { useEffect, useState } from 'react';
import { Zap, Globe, Menu, Search, BarChart3, MessageSquare } from 'lucide-react';
import { CitySelect } from './components/CitySelect';
import { DimensionSelect } from './components/DimensionSelect';
import { JobProgress } from './components/JobProgress';
import { Chat } from './components/Chat';
import { Results } from './components/Results';
import { JobRequest, startJob, getJobResults, CityResult } from './api';

function App() {
  const [cities, setCities] = useState<string[]>([]);
  const [dims, setDims] = useState<string[]>([]);
  const [depth, setDepth] = useState<"standard" | "deep">("standard");
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<CityResult[]>([]);
  const [isScraping, setIsScraping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

useEffect(() => {
    // Attempt to log mount
  }, []);

  const handleStartJob = async (req?: JobRequest) => {
    const request = req || { cities, dimensions: dims, depth };

    if (!request.cities.length) {
      alert("Please select at least one city.");
      return;
    }

    if (req) {
      setCities(req.cities);
      if (req.dimensions) setDims(req.dimensions);
      if (req.depth) setDepth(req.depth);
    }

    try {
      setIsScraping(true);
      setResults([]);
      const id = await startJob(request);
      setJobId(id);
    } catch (e) {
      alert("Failed to start job: " + e);
      setIsScraping(false);
    }
  };

  const handleJobComplete = async () => {
    if (!jobId) return;
    try {
      const res = await getJobResults(jobId);
      setResults(res.cities);
    } catch (e) {
      console.error(e);
    } finally {
      setIsScraping(false);
    }
  };

  return (
    <div 
      style={{ 
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#0a0f14', 
        color: '#e5e7eb',
        fontFamily: 'Inter, system-ui, sans-serif',
        backgroundImage: 'radial-gradient(circle at 50% 0%, #111827 0%, #000000 100%)'
      }}
    >
      
      {/* Sidebar */}
      <aside 
        style={{
          width: '380px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid rgba(255,255,255,0.1)',
          background: 'rgba(10, 15, 20, 0.75)',
          backdropFilter: 'blur(12px)',
          transition: 'transform 0.3s',
          transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
          position: 'relative',
          zIndex: 40
        }}
      >
        {/* Brand Header */}
        <div style={{ padding: '32px', paddingBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <h1 style={{ 
            fontSize: '24px', 
            fontWeight: 800, 
            margin: 0,
            background: 'linear-gradient(to bottom right, #ffffff, #9ca3af)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Our City Health
          </h1>
          <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '8px', letterSpacing: '0.05em', textTransform: 'uppercase', opacity: 0.7, fontWeight: 500 }}>
            Corporate Intelligence Unit
          </p>
        </div>

        {/* Configuration */}
        <div style={{ padding: '32px', flex: 1, overflowY: 'auto' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Target Portfolio</label>
              <CitySelect selected={cities} onChange={setCities} />
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Focus Dimensions</label>
              <DimensionSelect selected={dims} onChange={setDims} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Analysis Depth</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <button 
                  onClick={() => setDepth('standard')}
                  style={{
                    padding: '12px 16px',
                    fontSize: '14px',
                    fontWeight: 500,
                    borderRadius: '12px',
                    border: depth === 'standard' ? '1px solid #22c55e' : '1px solid transparent',
                    background: depth === 'standard' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    color: depth === 'standard' ? '#22c55e' : '#9ca3af',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Standard
                </button>
                <button 
                  onClick={() => setDepth('deep')}
                  style={{
                    padding: '12px 16px',
                    fontSize: '14px',
                    fontWeight: 500,
                    borderRadius: '12px',
                    border: depth === 'deep' ? '1px solid #22c55e' : '1px solid transparent',
                    background: depth === 'deep' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    color: depth === 'deep' ? '#22c55e' : '#9ca3af',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Deep Scrape
                </button>
              </div>
              <p style={{ fontSize: '11px', color: '#6b7280', margin: 0, lineHeight: 1.5 }}>
                {depth === 'standard' ? 'Rapid analysis of top 20 trusted sources.' : 'Comprehensive deep-dive (~3 mins/city).'}
              </p>
            </div>
          </div>
        </div>

        {/* Action Area */}
        <div style={{ padding: '32px', borderTop: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.2)' }}>
          <button 
            onClick={() => handleStartJob()}
            disabled={isScraping || cities.length === 0}
            style={{
              width: '100%',
              padding: '16px',
              background: '#22c55e',
              color: '#000',
              fontWeight: 700,
              borderRadius: '12px',
              border: 'none',
              cursor: isScraping || cities.length === 0 ? 'not-allowed' : 'pointer',
              opacity: isScraping || cities.length === 0 ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              boxShadow: isScraping || cities.length === 0 ? 'none' : '0 0 20px rgba(34,197,94,0.3)',
              transition: 'all 0.3s'
            }}
          >
            {isScraping ? (
              <span>Processing...</span>
            ) : (
              <>
                <Zap size={18} fill="black" />
                <span>Initialize Analysis</span>
              </>
            )}
          </button>
          
          {jobId && isScraping && (
             <div style={{ marginTop: '16px' }}>
               <JobProgress jobId={jobId} onComplete={handleJobComplete} />
             </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
        {/* Top Nav */}
        <header style={{ 
          height: '80px', 
          borderBottom: '1px solid rgba(255,255,255,0.1)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          padding: '0 32px',
          background: 'rgba(0,0,0,0.2)',
          backdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 30
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '14px', fontWeight: 500, color: '#9ca3af' }}>
                <Globe size={16} />
                <span style={{ opacity: 0.3 }}>/</span>
                <span style={{ color: '#e5e7eb' }}>Global Dashboard</span>
            </div>
            
            {results.length > 0 && (
                <button 
                  onClick={() => setResults([])} 
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 500,
                    color: '#9ca3af',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                    <BarChart3 size={14} /> Reset View
                </button>
            )}
        </header>

        <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
           {results.length > 0 ? (
             <div style={{ maxWidth: '1280px', margin: '0 auto', paddingBottom: '80px' }}>
               <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '24px', marginBottom: '32px' }}>
                 <div>
                    <h2 style={{ fontSize: '30px', fontWeight: 700, color: 'white', letterSpacing: '-0.02em', margin: 0 }}>Intelligence Report</h2>
                    <p style={{ color: '#9ca3af', marginTop: '8px', fontSize: '14px', margin: 0 }}>Generated for <span style={{ color: '#22c55e', fontFamily: 'monospace' }}>{cities.length}</span> markets</p>
                 </div>
               </div>
               <Results results={results} />
             </div>
           ) : (
             <div style={{ height: '100%', maxWidth: '1024px', margin: '0 auto', display: 'flex', flexDirection: 'column', justifyContent: 'center', paddingBottom: '80px' }}>
                <div style={{ flex: 1, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(10, 15, 20, 0.75)', backdropFilter: 'blur(12px)' }}>
                    <Chat jobId={jobId || undefined} onJobRequest={handleStartJob} />
                </div>
             </div>
           )}
        </div>
      </main>
    </div>
  )
}

export default App
