// Graph Exploration Page

'use client';

import React, { useState, useEffect } from 'react';

interface GraphStats {
    nodes: {
        functions: number;
        classes: number;
        files: number;
    };
    relationships: {
        calls: number;
        contains: number;
        imports: number;
    };
    total_nodes: number;
    total_relationships: number;
}

export default function GraphPage() {
    const [stats, setStats] = useState<GraphStats | null>(null);
    const [selectedFunction, setSelectedFunction] = useState('');
    const [callers, setCallers] = useState<any[]>([]);
    const [callees, setCallees] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        loadGraphStats();
    }, []);

    const loadGraphStats = async () => {
        try {
            const response = await fetch('http://localhost:8000/graph/overview');
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to load graph stats:', error);
        }
    };

    const handleFunctionLookup = async () => {
        if (!selectedFunction.trim()) return;

        setIsLoading(true);

        try {
            // Get callers
            const callersResponse = await fetch(
                `http://localhost:8000/graph/function/${selectedFunction}/callers`
            );
            const callersData = await callersResponse.json();
            setCallers(callersData.callers || []);

            // Get callees
            const calleesResponse = await fetch(
                `http://localhost:8000/graph/function/${selectedFunction}/callees`
            );
            const calleesData = await calleesResponse.json();
            setCallees(calleesData.callees || []);
        } catch (error) {
            console.error('Function lookup failed:', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-full overflow-y-auto">
            <div className="max-w-6xl mx-auto p-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Code Graph Explorer</h1>
                    <p className="text-slate-400">
                        Explore function call graphs and code dependencies
                    </p>
                </div>

                {/* Statistics */}
                {stats && (
                    <div className="mb-8">
                        <h2 className="text-xl font-semibold mb-4">Graph Overview</h2>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="card bg-indigo-900/30 border-indigo-700">
                                <div className="text-3xl font-bold text-indigo-400">
                                    {stats.nodes.functions}
                                </div>
                                <div className="text-sm text-slate-400">Functions</div>
                            </div>

                            <div className="card bg-purple-900/30 border-purple-700">
                                <div className="text-3xl font-bold text-purple-400">
                                    {stats.nodes.classes}
                                </div>
                                <div className="text-sm text-slate-400">Classes</div>
                            </div>

                            <div className="card bg-pink-900/30 border-pink-700">
                                <div className="text-3xl font-bold text-pink-400">
                                    {stats.nodes.files}
                                </div>
                                <div className="text-sm text-slate-400">Files</div>
                            </div>

                            <div className="card bg-green-900/30 border-green-700">
                                <div className="text-3xl font-bold text-green-400">
                                    {stats.relationships.calls}
                                </div>
                                <div className="text-sm text-slate-400">Call Relations</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Function Lookup */}
                <div className="card mb-8">
                    <h2 className="text-xl font-semibold mb-4">Function Call Graph</h2>

                    <div className="flex gap-2 mb-6">
                        <input
                            type="text"
                            value={selectedFunction}
                            onChange={(e) => setSelectedFunction(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleFunctionLookup()}
                            placeholder="Enter function name..."
                            className="input flex-1"
                        />
                        <button
                            onClick={handleFunctionLookup}
                            disabled={!selectedFunction.trim() || isLoading}
                            className="btn btn-primary"
                        >
                            {isLoading ? 'Loading...' : 'Explore'}
                        </button>
                    </div>

                    {/* Results */}
                    {(callers.length > 0 || callees.length > 0) && (
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Callers */}
                            <div>
                                <h3 className="font-semibold mb-3 text-indigo-400">
                                    ⬆️ Called By ({callers.length})
                                </h3>
                                {callers.length === 0 ? (
                                    <p className="text-sm text-slate-400">No callers found</p>
                                ) : (
                                    <div className="space-y-2">
                                        {callers.map((caller, idx) => (
                                            <div key={idx} className="bg-slate-900 rounded p-3">
                                                <div className="font-medium">{caller.name}</div>
                                                <div className="text-xs text-slate-400">{caller.file}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Callees */}
                            <div>
                                <h3 className="font-semibold mb-3 text-purple-400">
                                    ⬇️ Calls ({callees.length})
                                </h3>
                                {callees.length === 0 ? (
                                    <p className="text-sm text-slate-400">No callees found</p>
                                ) : (
                                    <div className="space-y-2">
                                        {callees.map((callee, idx) => (
                                            <div key={idx} className="bg-slate-900 rounded p-3">
                                                <div className="font-medium">{callee.name}</div>
                                                <div className="text-xs text-slate-400">{callee.file}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Info */}
                <div className="p-4 bg-slate-800 border border-slate-700 rounded-lg">
                    <h4 className="font-semibold mb-2">💡 Graph Capabilities</h4>
                    <ul className="space-y-1 text-sm text-slate-300">
                        <li>• Trace function call relationships</li>
                        <li>• Identify high-impact code changes</li>
                        <li>• Find circular dependencies</li>
                        <li>• Analyze code coupling</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
