import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, sendChat, JobRequest } from '../api';
import { Send, Bot, User as UserIcon, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Props {
    jobId?: string;
    onJobRequest: (req: JobRequest) => void;
}

export function Chat({ jobId, onJobRequest }: Props) {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<ChatMessage[]>([
        { role: "assistant", content: "I'm your corporate intelligence assistant. Configure your analysis on the left, or ask me to help you define the scope." }
    ]);
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages, loading]);

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg: ChatMessage = { role: "user", content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const resp = await sendChat([...messages, userMsg], jobId);
            setMessages(prev => [...prev, resp.message]);
            
            if (resp.job_request) {
                onJobRequest(resp.job_request);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I had trouble connecting to the intelligence engine." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-transparent">
            {/* Header / Context Indicator */}
            <div className="px-8 py-4 border-b border-white/10 bg-white/5 backdrop-blur-md flex items-center justify-between" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                <div className="flex items-center gap-3">
                    <Sparkles size={16} className={jobId ? "text-emerald-500 drop-shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "text-gray-500"} />
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                        {jobId ? "Grounded Context Active" : "General Assistant Mode"}
                    </span>
                </div>
                {jobId && (
                    <span className="text-[10px] bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full border border-emerald-500/20 font-mono tracking-tight">
                        JOB: {jobId.slice(0, 6)}
                    </span>
                )}
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar" ref={scrollRef} style={{ scrollBehavior: 'smooth' }}>
                {messages.map((m, i) => (
                    <div key={i} className={`flex gap-5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`} style={{ animation: 'fadeIn 0.3s ease-out' }}>
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${
                            m.role === 'assistant' 
                                ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' 
                                : 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
                        }`}
                        style={{ background: m.role === 'assistant' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)' }}>
                            {m.role === 'assistant' ? <Bot size={20} color="#10b981" /> : <UserIcon size={20} color="#3b82f6" />}
                        </div>
                        
                        <div className={`p-5 rounded-2xl max-w-[85%] text-sm leading-relaxed shadow-xl backdrop-blur-sm ${
                            m.role === 'assistant' 
                                ? 'glass-panel text-gray-200 rounded-tl-sm' 
                                : 'text-white rounded-tr-sm font-medium border border-blue-500/20'
                        }`}
                        style={{ 
                            background: m.role === 'assistant' ? 'rgba(10, 15, 20, 0.6)' : 'rgba(59, 130, 246, 0.8)',
                            border: '1px solid rgba(255,255,255,0.1)'
                        }}>
                            <div className="prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown components={{
                                    p: ({node, ...props}) => <p className="mb-3 last:mb-0 leading-relaxed" {...props} />,
                                    ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-3 space-y-1" {...props} />,
                                    ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-3 space-y-1" {...props} />,
                                    strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                                }}>
                                    {m.content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    </div>
                ))}
                
                {loading && (
                    <div className="flex gap-5" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 border border-emerald-500/20">
                            <Bot size={20} className="text-emerald-500" />
                        </div>
                        <div className="p-5 rounded-2xl rounded-tl-sm flex items-center gap-3" style={{ background: 'rgba(10, 15, 20, 0.6)', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <Loader2 className="animate-spin text-emerald-500" size={18} />
                            <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">Analyzing Intelligence...</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-8 pt-4">
                <form onSubmit={handleSubmit} className="relative group">
                    <input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder={jobId ? "Ask questions based on the scraped data..." : "E.g., 'Analyze the housing crisis in New York'"}
                        className="relative w-full bg-black/40 border border-white/20 rounded-2xl py-5 pl-6 pr-16 text-sm focus:outline-none transition-all placeholder:text-gray-500 text-gray-200 shadow-xl backdrop-blur-xl"
                        style={{ background: 'rgba(0,0,0,0.4)', color: 'white' }}
                    />
                    <button 
                        type="submit"
                        disabled={!input.trim() || loading}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-3 text-emerald-500 hover:bg-emerald-500/10 rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        <Send size={20} color="#10b981" />
                    </button>
                </form>
                <div className="text-center mt-4 flex items-center justify-center gap-2 opacity-40 hover:opacity-80 transition-opacity">
                    <AlertCircle size={12} className="text-gray-400" />
                    <span className="text-[10px] text-gray-400 font-medium tracking-wide">
                        AI-GENERATED INTELLIGENCE. VERIFY CRITICAL SOURCES.
                    </span>
                </div>
            </div>
        </div>
    );
}
