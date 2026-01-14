import React from 'react';
import { CityResult } from '../api';
import { AlertTriangle, ExternalLink, TrendingUp, MessageSquare, BarChart } from 'lucide-react';

interface Props {
    results: CityResult[];
}

export function Results({ results }: Props) {
    if (!results.length) return null;

    return (
        <div className="grid grid-cols-1 gap-10">
            {results.map((city, idx) => (
                <div 
                    key={city.city_name} 
                    className="rounded-2xl overflow-hidden group transition-colors duration-500"
                    style={{ 
                        animationDelay: `${idx * 100}ms`,
                        animation: 'fadeIn 0.5s ease-out forwards',
                        background: 'rgba(10, 15, 20, 0.75)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
                    }}
                >
                    {/* Hero Header */}
                    <div className="p-8 border-b border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-6" 
                         style={{ background: 'linear-gradient(90deg, rgba(34,197,94,0.05), transparent)' }}>
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h2 className="text-4xl font-extrabold text-white tracking-tight" style={{ fontFamily: 'Inter, sans-serif' }}>{city.city_name}</h2>
                                <span className="px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold tracking-widest uppercase">
                                    Analyzed
                                </span>
                            </div>
                            <div className="flex items-center gap-4 text-xs font-medium text-gray-400">
                                <span className="flex items-center gap-1.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-white/50"></div>
                                    {city.citations.length} Sources Processed
                                </span>
                                {city.reddit_posts.length > 0 && (
                                    <span className="flex items-center gap-1.5" style={{ color: '#FF4500' }}>
                                        <MessageSquare size={12} />
                                        {city.reddit_posts.length} Community Threads
                                    </span>
                                )}
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-5 bg-black/30 p-4 rounded-xl border border-white/5 backdrop-blur-md">
                            <div className="text-right">
                                <div className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-0.5">Health Index</div>
                                <div className="text-[10px] text-gray-500 font-medium">AI Weighted Score</div>
                            </div>
                            <div className="h-12 w-[1px] bg-white/10"></div>
                            <div className={`text-5xl font-black font-mono tracking-tighter drop-shadow-2xl`}
                                 style={{ 
                                     color: city.overall_health >= 70 ? '#34d399' : city.overall_health >= 50 ? '#facc15' : '#fb7185',
                                     textShadow: city.overall_health >= 70 ? '0 0 20px rgba(52, 211, 153, 0.5)' : 'none'
                                 }}>
                                {city.overall_health}
                            </div>
                        </div>
                    </div>

                    <div className="p-8 grid grid-cols-1 lg:grid-cols-12 gap-10">
                        {/* Metrics Column */}
                        <div className="lg:col-span-7 space-y-8">
                            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                                    <BarChart size={16} className="text-emerald-500" /> 
                                    Dimension Metrics
                                </h3>
                                <span className="text-[10px] text-gray-400 bg-white/5 px-2 py-1 rounded">12 Key Indicators</span>
                            </div>
                            
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-6">
                                {Object.entries(city.category_scores).map(([dim, data]) => (
                                    <div key={dim} className="relative">
                                        <div className="flex justify-between items-end mb-2">
                                            <span className="text-sm font-medium text-gray-300 capitalize">{dim.replace('_', ' ')}</span>
                                            <span className="text-sm font-mono font-bold" style={{ color: data.score >= 50 ? '#34d399' : '#fb923c' }}>
                                                {data.score}
                                            </span>
                                        </div>
                                        <div className="h-1.5 bg-black/40 rounded-full overflow-hidden mb-2 border border-white/5">
                                            <div 
                                                className="h-full rounded-full transition-all duration-1000"
                                                style={{ 
                                                    width: `${data.score}%`,
                                                    backgroundColor: data.score >= 50 ? '#34d399' : '#fb923c',
                                                    boxShadow: data.score >= 50 ? '0 0 8px rgba(52, 211, 153, 0.4)' : 'none'
                                                }}
                                            />
                                        </div>
                                        <p className="text-[11px] text-gray-400 leading-relaxed line-clamp-1 hover:line-clamp-none transition-all cursor-help">
                                            {data.rationale}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Insights Column */}
                        <div className="lg:col-span-5 space-y-8 flex flex-col">
                            {/* Critical Issues */}
                            <div className="p-6 rounded-xl border-l-4" style={{ background: 'rgba(10, 15, 20, 0.6)', borderLeftColor: 'rgba(244, 63, 94, 0.5)' }}>
                                <h3 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                                    <AlertTriangle size={14} /> 
                                    Identified Friction Points
                                </h3>
                                <div className="space-y-4">
                                    {city.top_issues.slice(0, 4).map((issue, i) => (
                                        <div key={i} className="flex gap-3 items-start group">
                                            <span className="text-rose-500/40 font-mono text-xs mt-0.5">0{i+1}</span>
                                            <div>
                                                <span className="text-sm font-bold text-gray-200 block group-hover:text-white transition-colors">{issue.name}</span>
                                                <span className="text-xs text-gray-400 leading-relaxed block mt-1">{issue.why_it_matters}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Citations */}
                            <div className="flex-1 bg-black/20 rounded-xl p-6 border border-white/5">
                                <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <ExternalLink size={14} /> 
                                    Intelligence Sources
                                </h3>
                                <div className="flex flex-wrap gap-2 content-start">
                                    {city.citations.slice(0, 12).map((url, i) => {
                                        let hostname = "";
                                        try { hostname = new URL(url).hostname.replace('www.', ''); } catch(e) {}
                                        return (
                                            <a 
                                                key={i} 
                                                href={url} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="px-3 py-1.5 bg-white/5 hover:bg-blue-500/20 text-[11px] text-gray-400 hover:text-white rounded-md border border-white/5 hover:border-blue-500/30 transition-all truncate max-w-[140px] flex items-center gap-1.5 group"
                                                title={url}
                                                style={{ textDecoration: 'none' }}
                                            >
                                                <div className="w-1 h-1 rounded-full bg-blue-500/50 group-hover:bg-blue-500"></div>
                                                {hostname}
                                            </a>
                                        );
                                    })}
                                    {city.citations.length > 12 && (
                                        <button className="px-3 py-1.5 bg-transparent text-[11px] text-gray-400 hover:text-white rounded-md border border-white/10 hover:border-white/30 transition-all">
                                            View +{city.citations.length - 12} more
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
