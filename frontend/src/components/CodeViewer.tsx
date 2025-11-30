// Monaco Code Viewer Component

'use client';

import React, { useRef, useEffect } from 'react';
import * as monaco from 'monaco-editor';

interface CodeViewerProps {
    code: string;
    language: string;
    filePath?: string;
    readOnly?: boolean;
    lineNumbers?: boolean;
    minimap?: boolean;
    highlightLine?: number;
    onLineClick?: (lineNumber: number) => void;
}

export default function CodeViewer({
    code,
    language,
    filePath,
    readOnly = true,
    lineNumbers = true,
    minimap = true,
    highlightLine,
    onLineClick,
}: CodeViewerProps) {
    const editorRef = useRef<HTMLDivElement>(null);
    const monacoRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

    useEffect(() => {
        if (!editorRef.current) return;

        // Create Monaco editor
        const editor = monaco.editor.create(editorRef.current, {
            value: code,
            language: getMonacoLanguage(language),
            theme: 'vs-dark',
            readOnly,
            automaticLayout: true,
            lineNumbers: lineNumbers ? 'on' : 'off',
            minimap: {
                enabled: minimap,
            },
            scrollBeyondLastLine: false,
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Courier New', monospace",
            padding: { top: 10, bottom: 10 },
            renderLineHighlight: 'all',
            scrollbar: {
                verticalScrollbarSize: 10,
                horizontalScrollbarSize: 10,
            },
        });

        monacoRef.current = editor;

        // Handle line clicks
        if (onLineClick) {
            editor.onMouseDown((e) => {
                if (e.target.position) {
                    onLineClick(e.target.position.lineNumber);
                }
            });
        }

        // Cleanup
        return () => {
            editor.dispose();
        };
    }, []);

    // Update code when it changes
    useEffect(() => {
        if (monacoRef.current) {
            const model = monacoRef.current.getModel();
            if (model && model.getValue() !== code) {
                model.setValue(code);
            }
        }
    }, [code]);

    // Highlight specific line
    useEffect(() => {
        if (monacoRef.current && highlightLine) {
            monacoRef.current.revealLineInCenter(highlightLine);
            monacoRef.current.setPosition({
                lineNumber: highlightLine,
                column: 1,
            });

            // Add decoration for highlighted line
            monacoRef.current.deltaDecorations(
                [],
                [
                    {
                        range: new monaco.Range(highlightLine, 1, highlightLine, 1),
                        options: {
                            isWholeLine: true,
                            className: 'highlighted-line',
                            glyphMarginClassName: 'highlighted-line-glyph',
                        },
                    },
                ]
            );
        }
    }, [highlightLine]);

    return (
        <div className="w-full h-full border border-slate-700 rounded-lg overflow-hidden">
            {/* Header */}
            {filePath && (
                <div className="bg-slate-800 border-b border-slate-700 px-4 py-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-mono text-slate-300">{filePath}</span>
                        <span className="text-xs text-slate-500">({language})</span>
                    </div>
                    {readOnly && (
                        <span className="text-xs text-slate-500">Read Only</span>
                    )}
                </div>
            )}

            {/* Monaco Editor */}
            <div ref={editorRef} className="w-full h-full min-h-[400px]" />

            <style jsx global>{`
        .highlighted-line {
          background-color: rgba(99, 102, 241, 0.2) !important;
        }
        .highlighted-line-glyph {
          background-color: rgb(99, 102, 241) !important;
          width: 3px !important;
        }
      `}</style>
        </div>
    );
}

// Map language names to Monaco language IDs
function getMonacoLanguage(lang: string): string {
    const languageMap: Record<string, string> = {
        python: 'python',
        py: 'python',
        typescript: 'typescript',
        ts: 'typescript',
        javascript: 'javascript',
        js: 'javascript',
        jsx: 'javascript',
        tsx: 'typescript',
        json: 'json',
        html: 'html',
        css: 'css',
        scss: 'scss',
        markdown: 'markdown',
        md: 'markdown',
        yaml: 'yaml',
        yml: 'yaml',
    };

    return languageMap[lang.toLowerCase()] || 'plaintext';
}
