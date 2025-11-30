// Zustand Store for Global State Management

import { create } from 'zustand';

interface IndexingState {
    isIndexing: boolean;
    progress: number;
    status: string;
    sessionId: string | null;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface ChatState {
    messages: ChatMessage[];
    isStreaming: boolean;
    sessionId: string | null;
}

interface Store {
    // Indexing state
    indexing: IndexingState;
    setIndexing: (state: Partial<IndexingState>) => void;

    // Chat state
    chat: ChatState;
    addMessage: (message: ChatMessage) => void;
    clearChat: () => void;
    setStreaming: (isStreaming: boolean) => void;

    // UI state
    sidebarOpen: boolean;
    toggleSidebar: () => void;

    // Current file/function
    selectedFile: string | null;
    selectedFunction: string | null;
    setSelectedFile: (file: string | null) => void;
    setSelectedFunction: (func: string | null) => void;
}

export const useStore = create<Store>((set) => ({
    // Indexing
    indexing: {
        isIndexing: false,
        progress: 0,
        status: '',
        sessionId: null,
    },
    setIndexing: (state) =>
        set((prev) => ({
            indexing: { ...prev.indexing, ...state },
        })),

    // Chat
    chat: {
        messages: [],
        isStreaming: false,
        sessionId: null,
    },
    addMessage: (message) =>
        set((prev) => ({
            chat: {
                ...prev.chat,
                messages: [...prev.chat.messages, message],
            },
        })),
    clearChat: () =>
        set((prev) => ({
            chat: {
                ...prev.chat,
                messages: [],
            },
        })),
    setStreaming: (isStreaming) =>
        set((prev) => ({
            chat: {
                ...prev.chat,
                isStreaming,
            },
        })),

    // UI
    sidebarOpen: true,
    toggleSidebar: () =>
        set((prev) => ({ sidebarOpen: !prev.sidebarOpen })),

    // Selection
    selectedFile: null,
    selectedFunction: null,
    setSelectedFile: (file) => set({ selectedFile: file }),
    setSelectedFunction: (func) => set({ selectedFunction: func }),
}));
