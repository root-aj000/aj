// Index Page - Repository Indexing

'use client';

import React, { useState, useEffect } from 'react';
import { useStore } from '@/store';

export default function IndexPage() {
    const { indexing, setIndexing } = useStore();
    const [repoPath, setRepoPath] = useState('');

    const startIndexing = async () => {
        try {
            const response = await fetch('http://localhost:8000/index_file/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repo_path: repoPath,
                    force_reindex: false,
                }),
            });

            const data = await response.json();

            setIndexing({
                isIndexing: true,
                sessionId: data.session_id,
                progress: 0,
                status: 'Started...',
            });

            // Poll for status
            pollStatus(data.session_id);
        } catch (error) {
            console.error('Failed to start indexing:', error);
        }
    };

    const pollStatus = async (sessionId: string) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/index_file/status/${sessionId}`);
                const data = await response.json();

                setIndexing({
                    progress: data.progress,
                    status: data.message,
                });

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(interval);
                    setIndexing({ isIndexing: false });
                }
            } catch (error) {
                clearInterval(interval);
                setIndexing({ isIndexing: false });
            }
        }, 1000);
    };

    return (
        <div className="h-full overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Repository Indexing</h1>
                    <p className="text-slate-400">
                        Index your codebase to enable AI-powered search, chat, and debugging
                    </p>
                </div>

                {/* Indexing Form */}
                <div className="card mb-6">
                    <h2 className="text-xl font-semibold mb-4">Start New Index</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Repository Path</label>
                            <input
                                type="text"
                                value={repoPath}
                                onChange={(e) => setRepoPath(e.target.value)}
                                placeholder="/path/to/your/repository"
                                className="input"
                                disabled={indexing.isIndexing}
                            />
                        </div>

                        <button
                            onClick={startIndexing}
                            disabled={!repoPath || indexing.isIndexing}
                            className="btn btn-primary w-full"
                        >
                            {indexing.isIndexing ? 'Indexing...' : 'Start Indexing'}
                        </button>
                    </div>
                </div>

                {/* Progress */}
                {indexing.isIndexing && (
                    <div className="card">
                        <h3 className="text-lg font-semibold mb-4">Indexing Progress</h3>

                        <div className="mb-4">
                            <div className="flex justify-between text-sm mb-2">
                                <span>{indexing.status}</span>
                                <span>{Math.round(indexing.progress * 100)}%</span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-3">
                                <div
                                    className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                                    style={{ width: `${indexing.progress * 100}%` }}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="bg-slate-900 rounded p-3">
                                <div className="text-slate-400">Session ID</div>
                                <div className="font-mono text-xs">{indexing.sessionId}</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Statistics */}
                <div className="card mt-6">
                    <h3 className="text-lg font-semibold mb-4">Index Statistics</h3>

                    <div className="grid grid-cols-3 gap-4">
                        <div className="bg-slate-900 rounded p-4 text-center">
                            <div className="text-3xl font-bold text-indigo-400">0</div>
                            <div className="text-sm text-slate-400">Files Indexed</div>
                        </div>
                        <div className="bg-slate-900 rounded p-4 text-center">
                            <div className="text-3xl font-bold text-purple-400">0</div>
                            <div className="text-sm text-slate-400">Functions</div>
                        </div>
                        <div className="bg-slate-900 rounded p-4 text-center">
                            <div className="text-3xl font-bold text-pink-400">0</div>
                            <div className="text-sm text-slate-400">Chunks</div>
                        </div>
                    </div>
                </div>

                {/* Instructions */}
                <div className="mt-6 p-4 bg-slate-800 border border-slate-700 rounded-lg">
                    <h4 className="font-semibold mb-2">📝 What happens during indexing?</h4>
                    <ul className="space-y-1 text-sm text-slate-300">
                        <li>• Discovers all source files in the repository</li>
                        <li>• Parses code into Abstract Syntax Trees</li>
                        <li>• Generates semantic embeddings for search</li>
                        <li>• Builds code graph for relationships</li>
                        <li>• Analyzes code health and quality</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
