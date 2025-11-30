// Root Layout for Next.js App

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Layout from '@/components/Layout';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Vibe Agent - AI Coding Assistant',
    description: 'Local-first AI coding assistant with semantic search and intelligent debugging',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <Layout>{children}</Layout>
            </body>
        </html>
    );
}
