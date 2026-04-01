import React, { useEffect, useState } from 'react';
import { JobStatus } from '../api';
import { Loader2, CheckCircle2, AlertCircle, Terminal, Activity } from 'lucide-react';

interface Props {
    jobId: string;
    onComplete: () => void;
}

export function JobProgress({ jobId, onComplete }: Props) {
    const [status, setStatus] = useState<JobStatus | null>(null);

    useEffect(() => {
        const evtSource = new EventSource(`/api/jobs/${jobId}/events`);
        
        evtSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setStatus(data);
            if (data.status === 'completed' || data.status === 'failed') {
                evtSource.close();
                if (data.status === 'completed') {
                    onComplete();
                }
            }
        };

        evtSource.onerror = () => {
            evtSource.close();
        };

        return () => evtSource.close();
    }, [jobId, onComplete]);

    if (!status) return (
        <div className="glass-panel rounded-xl p-4 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-1/2 mb-3"></div>
            <div className="h-1.5 bg-white/5 rounded w-full"></div>
        </div>
    );

    return (
        <div className="glass-panel rounded-xl overflow-hidden animate-fade-in relative group">
            {/* Background Glow */}
            <div className="absolute inset-0 bg-brand-primary/5 group-hover:bg-brand-primary/10 transition-colors duration-500"></div>
            
            <div className="relative p-4 border-b border-brand-muted/10 flex items-center justify-between bg-black/20">
                <div className="flex items-center gap-3">
                    {status.status === 'running' && <Loader2 className="animate-spin text-brand-primary" size={16} />}
                    {status.status === 'completed' && <CheckCircle2 className="text-brand-primary" size={16} />}
                    {status.status === 'failed' && <AlertCircle className="text-rose-500" size={16} />}
                    <span className="text-xs font-bold text-white uppercase tracking-widest">{status.status}</span>
                </div>
                <div className="flex items-center gap-2">
                    <Activity size={12} className="text-brand-primary animate-pulse" />
                    <span className="text-xs font-mono font-bold text-brand-primary">{status.progress}%</span>
                </div>
            </div>
            
            <div className="relative p-4 space-y-4">
                <div className="h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                    <div 
                        className="h-full bg-brand-primary shadow-[0_0_15px_rgba(34,197,94,0.6)] transition-all duration-500 ease-out"
                        style={{ width: `${status.progress}%` }}
                    />
                </div>
                
                <div className="flex gap-3 items-start text-[11px] text-brand-muted font-mono bg-black/40 p-3 rounded-lg border border-white/5">
                    <Terminal size={12} className="mt-0.5 text-brand-primary opacity-70" />
                    <span className="line-clamp-2 leading-relaxed tracking-tight">{status.message}</span>
                </div>
            </div>
        </div>
    );
}
