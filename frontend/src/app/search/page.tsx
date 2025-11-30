// Search Page - Semantic Code Search

'use client';

import React, { useState } from 'react';

interface SearchResult {
    chunk_id: string;
    file_path: string;
    start_line: number;
    end_line: number;
    content: string;
    score: float;
    language: string;
}

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setIsSearching(true);

        try {
            const response = await fetch('http://localhost:8000/search/semantic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    top_k: 20,
                }),
            });

            const data = await response.json();
            setResults(data.results || []);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <header className="bg-slate-800 border-b border-slate-700 p-6">
                <h1 className="text-2xl font-bold mb-4">Semantic Code Search</h1>

                <div className="flex gap-2">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search for functions, classes, or concepts..."
                        className="input flex-1"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={!query.trim() || isSearching}
                        className="btn btn-primary"
                    >
                        {isSearching ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </header>

            {/* Results */}
            <div className="flex-1 overflow-y-auto p-6">
                {results.length === 0 && !isSearching && (
                    <div className="text-center text-slate-400 mt-20">
                        <h3 className="text-xl mb-2">🔍 Search Your Codebase</h3>
                        <p className="text-sm">Try natural language queries like:</p>
                        <ul className="space-y-1 text-sm mt-2">
                            <li>"authentication functions"</li>
                            <li>"database connection code"</li>
                            <li>"error handling logic"</li>
                        </ul>
                    </div>
                )}

                {isSearching && (
                    <div className="text-center text-slate-400 mt-20">
                        <div className="text-4xl mb-4">⏳</div>
                        <p>Searching...</p>
                    </div>
                )}

                {results.length > 0 && (
                    <div className="max-w-5xl mx-auto space-y-4">
                        <div className="text-sm text-slate-400 mb-4">
                            Found {results.length} results
                        </div>

                        {results.map((result, idx) => (
                            <div key={idx} className="card-hover">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h3 className="font-medium text-indigo-400">{result.file_path}</h3>
                                        <p className="text-sm text-slate-400">
                                            Lines {result.start_line}-{result.end_line} • {result.language}
                                        </p>
                                    </div>
                                    <div className="text-sm font-semibold text-green-400">
                                        {(result.score * 100).toFixed(1)}%
                                    </div>
                                </div>

                                <pre className="bg-slate-900 rounded p-3 overflow-x-auto text-sm">
                                    <code>{result.content}</code>
                                </pre>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
