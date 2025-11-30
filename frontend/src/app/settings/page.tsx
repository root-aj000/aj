// Settings Page

'use client';

import React, { useState, useEffect } from 'react';

export default function SettingsPage() {
    const [settings, setSettings] = useState({
        repoPath: '',
        geminiApiKey: '',
        llmModel: 'gemini-2.0-flash-exp',
        chunkSize: 400,
        chunkOverlap: 70,
        useLocalEmbeddings: true,
    });

    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        // In production, this would save to backend/localStorage
        localStorage.setItem('vibe-settings', JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    useEffect(() => {
        // Load saved settings
        const savedSettings = localStorage.getItem('vibe-settings');
        if (savedSettings) {
            setSettings(JSON.parse(savedSettings));
        }
    }, []);

    return (
        <div className="h-full overflow-y-auto">
            <div className="max-w-3xl mx-auto p-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Settings</h1>
                    <p className="text-slate-400">Configure Vibe Agent for your needs</p>
                </div>

                {/* General Settings */}
                <div className="card mb-6">
                    <h2 className="text-xl font-semibold mb-4">General</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Default Repository Path
                            </label>
                            <input
                                type="text"
                                value={settings.repoPath}
                                onChange={(e) => setSettings({ ...settings, repoPath: e.target.value })}
                                placeholder="/path/to/your/code"
                                className="input"
                            />
                            <p className="text-xs text-slate-400 mt-1">
                                Default path for indexing operations
                            </p>
                        </div>
                    </div>
                </div>

                {/* LLM Settings */}
                <div className="card mb-6">
                    <h2 className="text-xl font-semibold mb-4">LLM Configuration</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Gemini API Key
                            </label>
                            <input
                                type="password"
                                value={settings.geminiApiKey}
                                onChange={(e) => setSettings({ ...settings, geminiApiKey: e.target.value })}
                                placeholder="Enter your API key"
                                className="input"
                            />
                            <p className="text-xs text-slate-400 mt-1">
                                Get your key from{' '}
                                <a
                                    href="https://makersuite.google.com/app/apikey"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-indigo-400 hover:underline"
                                >
                                    Google AI Studio
                                </a>
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Primary Model
                            </label>
                            <select
                                value={settings.llmModel}
                                onChange={(e) => setSettings({ ...settings, llmModel: e.target.value })}
                                className="input"
                            >
                                <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Recommended)</option>
                                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Indexing Settings */}
                <div className="card mb-6">
                    <h2 className="text-xl font-semibold mb-4">Indexing</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Chunk Size (tokens)
                            </label>
                            <input
                                type="number"
                                value={settings.chunkSize}
                                onChange={(e) => setSettings({ ...settings, chunkSize: parseInt(e.target.value) })}
                                className="input"
                                min="100"
                                max="1000"
                            />
                            <p className="text-xs text-slate-400 mt-1">
                                Default: 400 tokens per chunk
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Chunk Overlap (tokens)
                            </label>
                            <input
                                type="number"
                                value={settings.chunkOverlap}
                                onChange={(e) => setSettings({ ...settings, chunkOverlap: parseInt(e.target.value) })}
                                className="input"
                                min="0"
                                max="200"
                            />
                            <p className="text-xs text-slate-400 mt-1">
                                Default: 70 tokens overlap between chunks
                            </p>
                        </div>

                        <div>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.useLocalEmbeddings}
                                    onChange={(e) => setSettings({ ...settings, useLocalEmbeddings: e.target.checked })}
                                    className="w-4 h-4"
                                />
                                <span className="text-sm font-medium">Use Local Embeddings (BGE-M3)</span>
                            </label>
                            <p className="text-xs text-slate-400 mt-1 ml-6">
                                Privacy-first: All embeddings generated locally
                            </p>
                        </div>
                    </div>
                </div>

                {/* Save Button */}
                <div className="flex gap-2">
                    <button onClick={handleSave} className="btn btn-primary">
                        {saved ? '✓ Saved!' : 'Save Settings'}
                    </button>
                    {saved && (
                        <div className="flex items-center text-green-400 text-sm">
                            Settings saved successfully
                        </div>
                    )}
                </div>

                {/* Info */}
                <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
                    <h4 className="font-semibold mb-2 text-blue-400">ℹ️ Note</h4>
                    <p className="text-sm text-slate-300">
                        Some settings require restarting the backend server to take effect.
                        Settings are stored in your browser's local storage.
                    </p>
                </div>
            </div>
        </div>
    );
}
