import React, { useState } from 'react';
import { X, Check } from 'lucide-react';

const DIMENSIONS = [
    "Affordability", "Services", "Safety", "Opportunity", "Culture", "Environment",
    "Transportation", "Governance", "Housing", "Economy", "Education", "Health"
];

interface Props {
    selected: string[];
    onChange: (dims: string[]) => void;
}

export function DimensionSelect({ selected, onChange }: Props) {
    const [isOpen, setIsOpen] = useState(false);

    const toggle = (dim: string) => {
        if (selected.includes(dim)) {
            onChange(selected.filter(d => d !== dim));
        } else {
            onChange([...selected, dim]);
        }
    };

    return (
        <div className="relative">
            <div 
                className="glass-button rounded-xl p-3.5 cursor-pointer flex justify-between items-center group hover:border-brand-muted/30"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={`text-sm font-medium ${selected.length ? 'text-white' : 'text-brand-muted'}`}>
                    {selected.length ? `${selected.length} Selected` : "Select dimensions..."}
                </span>
                <span className="text-brand-muted/50 text-[10px] group-hover:text-brand-primary transition-colors">▼</span>
            </div>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-20" onClick={() => setIsOpen(false)} />
                    <div className="absolute top-full left-0 right-0 mt-2 glass-panel rounded-xl max-h-[300px] overflow-y-auto z-30 animate-fade-in p-2 custom-scrollbar">
                        {DIMENSIONS.map(dim => (
                            <div 
                                key={dim}
                                className={`px-3 py-2.5 text-sm cursor-pointer rounded-lg flex items-center justify-between transition-colors mb-1 ${selected.includes(dim) ? 'bg-brand-secondary/10 text-brand-secondary' : 'text-brand-muted hover:bg-white/5 hover:text-white'}`}
                                onClick={() => toggle(dim)}
                            >
                                <span>{dim}</span>
                                {selected.includes(dim) && <Check size={14} />}
                            </div>
                        ))}
                    </div>
                </>
            )}

            <div className="flex flex-wrap gap-2 mt-3">
                {selected.map(dim => (
                    <div key={dim} className="bg-brand-secondary/10 border border-brand-secondary/20 text-brand-secondary text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-2 hover:bg-brand-secondary/20 transition-colors cursor-default">
                        {dim}
                        <X 
                            size={12} 
                            className="cursor-pointer opacity-60 hover:opacity-100 hover:text-white" 
                            onClick={() => toggle(dim)}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
