// Chat Page - Main Interface

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '@/store';

export default function ChatPage() {
    const { chat, addMessage, setStreaming } = useStore();
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chat.messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = {
            role: 'user' as const,
            content: input,
            timestamp: new Date(),
        };

        addMessage(userMessage);
        setInput('');
        setIsLoading(true);

        try {
            // Call API (placeholder - actual implementation would use API client)
            const response = await fetch('http://localhost:8000/chat/completion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [...chat.messages, userMessage].map((m) => ({
                        role: m.role,
                        content: m.content,
                    })),
                }),
            });

            const data = await response.json();

            addMessage({
                role: 'assistant',
                content: data.message || 'No response',
                timestamp: new Date(),
            });
        } catch (error) {
            addMessage({
                role: 'assistant',
                content: 'Error: Failed to get response',
                timestamp: new Date(),
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <header className="bg-slate-800 border-b border-slate-700 p-4">
                <h2 className="text-xl font-semibold">AI Chat Assistant</h2>
                <p className="text-sm text-slate-400">Ask about your code, debug errors, get suggestions</p>
            </header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chat.messages.length === 0 ? (
                    <div className="text-center text-slate-400 mt-20">
                        <h3 className="text-2xl mb-4">👋 Welcome to Vibe Agent</h3>
                        <p className="mb-2">Try asking:</p>
                        <ul className="space-y-1 text-sm">
                            <li>"How does authentication work?"</li>
                            <li>"Find all database queries"</li>
                            <li>"Explain the main function"</li>
                        </ul>
                    </div>
                ) : (
                    chat.messages.map((message, idx) => (
                        <div
                            key={idx}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-3xl rounded-lg p-4 ${message.role === 'user'
                                        ? 'bg-indigo-600 text-white'
                                        : 'bg-slate-800 border border-slate-700'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">
                                        {message.role === 'user' ? '👤' : '🤖'}
                                    </span>
                                    <div className="flex-1">
                                        <p className="whitespace-pre-wrap">{message.content}</p>
                                        <p className="text-xs opacity-70 mt-2">
                                            {message.timestamp.toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                            <div className="flex items-center gap-2">
                                <span className="text-2xl">🤖</span>
                                <span className="text-slate-400">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-slate-800 border-t border-slate-700 p-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask me anything about your code..."
                        className="input flex-1"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="btn btn-primary"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}
