import React, { useState } from 'react';
import { X, Check, Search } from 'lucide-react';

const CITIES = [
    "New York City", "Los Angeles", "San Francisco", "Chicago", "Seattle", "Boston",
    "London", "Paris", "Berlin", "Toronto", "Vancouver", "Sydney", "Melbourne",
    "Singapore", "Hong Kong", "Tokyo", "Seoul", "Mumbai", "Delhi", "Dubai",
    "Johannesburg", "Nairobi", "Mexico City", "Sao Paulo", "Rio de Janeiro",
    "Buenos Aires", "Madrid", "Barcelona", "Rome", "Amsterdam"
];

interface Props {
    selected: string[];
    onChange: (cities: string[]) => void;
}

export function CitySelect({ selected, onChange }: Props) {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");

    const toggle = (city: string) => {
        if (selected.includes(city)) {
            onChange(selected.filter(c => c !== city));
        } else {
            onChange([...selected, city]);
        }
    };

    const filtered = CITIES.filter(c => c.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="relative">
            <div 
                className="glass-button rounded-xl p-3.5 cursor-pointer flex justify-between items-center group hover:border-brand-muted/30"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={`text-sm font-medium ${selected.length ? 'text-white' : 'text-brand-muted'}`}>
                    {selected.length ? `${selected.length} Selected` : "Select markets..."}
                </span>
                <span className="text-brand-muted/50 text-[10px] group-hover:text-brand-primary transition-colors">▼</span>
            </div>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-20" onClick={() => setIsOpen(false)} />
                    <div className="absolute top-full left-0 right-0 mt-2 glass-panel rounded-xl max-h-[320px] flex flex-col z-30 animate-fade-in">
                        <div className="p-3 border-b border-brand-muted/10">
                             <div className="relative">
                                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted" />
                                <input 
                                    autoFocus
                                    className="w-full bg-black/20 text-sm rounded-lg py-2.5 pl-9 pr-3 focus:outline-none focus:ring-1 focus:ring-brand-primary/50 text-white placeholder:text-brand-muted/50 border border-brand-muted/10"
                                    placeholder="Search cities..."
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                    onClick={e => e.stopPropagation()}
                                />
                             </div>
                        </div>
                        <div className="overflow-y-auto flex-1 p-2 custom-scrollbar">
                            {filtered.map(city => (
                                <div 
                                    key={city}
                                    className={`px-3 py-2.5 text-sm cursor-pointer rounded-lg flex items-center justify-between transition-colors mb-1 ${selected.includes(city) ? 'bg-brand-primary/10 text-brand-primary' : 'text-brand-muted hover:bg-white/5 hover:text-white'}`}
                                    onClick={() => toggle(city)}
                                >
                                    <span>{city}</span>
                                    {selected.includes(city) && <Check size={14} />}
                                </div>
                            ))}
                            {filtered.length === 0 && (
                                <div className="p-4 text-center text-xs text-brand-muted">No results found</div>
                            )}
                        </div>
                    </div>
                </>
            )}

            <div className="flex flex-wrap gap-2 mt-3">
                {selected.map(city => (
                    <div key={city} className="bg-brand-primary/10 border border-brand-primary/20 text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-2 hover:bg-brand-primary/20 transition-colors cursor-default">
                        {city}
                        <X 
                            size={12} 
                            className="cursor-pointer opacity-60 hover:opacity-100 hover:text-white" 
                            onClick={() => toggle(city)}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
