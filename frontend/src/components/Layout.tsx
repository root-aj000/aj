// Main App Layout Component

import React from 'react';
import { useStore } from '@/store';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Layout({ children }: { children: React.ReactNode }) {
    const { sidebarOpen, toggleSidebar } = useStore();
    const pathname = usePathname();

    const navItems = [
        { href: '/', label: 'Chat', icon: '💬' },
        { href: '/index_file', label: 'Index', icon: '📁' },
        { href: '/search', label: 'Search', icon: '🔍' },
        { href: '/graph', label: 'Graph', icon: '🕸️' },
        { href: '/settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <div className="flex h-screen bg-slate-900">
            {/* Sidebar */}
            <aside
                className={`${sidebarOpen ? 'w-64' : 'w-20'
                    } bg-slate-800 border-r border-slate-700 transition-all duration-300 flex flex-col`}
            >
                {/* Logo */}
                <div className="p-4 border-b border-slate-700">
                    <h1 className={`font-bold text-xl gradient-text ${!sidebarOpen && 'text-center'}`}>
                        {sidebarOpen ? 'Vibe Agent' : 'VA'}
                    </h1>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-2">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${pathname === item.href
                                ? 'bg-indigo-600 text-white'
                                : 'text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            <span className="text-xl">{item.icon}</span>
                            {sidebarOpen && <span className="font-medium">{item.label}</span>}
                        </Link>
                    ))}
                </nav>

                {/* Toggle Button */}
                <button
                    onClick={toggleSidebar}
                    className="p-4 border-t border-slate-700 text-slate-400 hover:text-white transition-colors"
                >
                    {sidebarOpen ? '◀' : '▶'}
                </button>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden">{children}</main>
        </div>
    );
}
