// Diff Viewer Component

'use client';

import React, { useMemo } from 'react';
import { diffLines, Change } from 'diff';

interface DiffViewerProps {
    original: string;
    modified: string;
    fileName?: string;
    viewMode?: 'split' | 'unified';
    showLineNumbers?: boolean;
}

export default function DiffViewer({
    original,
    modified,
    fileName,
    viewMode = 'unified',
    showLineNumbers = true,
}: DiffViewerProps) {
    const diffResult = useMemo(() => {
        return diffLines(original, modified);
    }, [original, modified]);

    const stats = useMemo(() => {
        let additions = 0;
        let deletions = 0;

        diffResult.forEach((part: Change) => {
            if (part.added) additions += part.count || 0;
            if (part.removed) deletions += part.count || 0;
        });

        return { additions, deletions };
    }, [diffResult]);

    return (
        <div className="w-full border border-slate-700 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="bg-slate-800 border-b border-slate-700 px-4 py-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {fileName && (
                            <span className="text-sm font-mono text-slate-300">{fileName}</span>
                        )}
                        <div className="flex items-center gap-2 text-xs">
                            <span className="text-green-400">+{stats.additions}</span>
                            <span className="text-red-400">-{stats.deletions}</span>
                        </div>
                    </div>

                    {/* View mode toggle would go here */}
                </div>
            </div>

            {/* Diff Content */}
            <div className="bg-slate-900 overflow-x-auto">
                {viewMode === 'unified' ? (
                    <UnifiedDiff diff={diffResult} showLineNumbers={showLineNumbers} />
                ) : (
                    <SplitDiff original={original} modified={modified} showLineNumbers={showLineNumbers} />
                )}
            </div>
        </div>
    );
}

// Unified Diff View
function UnifiedDiff({ diff, showLineNumbers }: { diff: Change[]; showLineNumbers: boolean }) {
    let lineNumber = 0;

    return (
        <div className="font-mono text-sm">
            {diff.map((part, idx) => {
                const lines = part.value.split('\n').filter((line, i, arr) => {
                    // Filter out last empty line
                    return i < arr.length - 1 || line !== '';
                });

                return lines.map((line, lineIdx) => {
                    lineNumber++;
                    const bgColor = part.added
                        ? 'bg-green-900/30'
                        : part.removed
                            ? 'bg-red-900/30'
                            : 'bg-transparent';
                    const textColor = part.added
                        ? 'text-green-300'
                        : part.removed
                            ? 'text-red-300'
                            : 'text-slate-300';
                    const prefix = part.added ? '+' : part.removed ? '-' : ' ';
                    const borderColor = part.added
                        ? 'border-l-2 border-green-500'
                        : part.removed
                            ? 'border-l-2 border-red-500'
                            : '';

                    return (
                        <div
                            key={`${idx}-${lineIdx}`}
                            className={`flex items-start ${bgColor} ${borderColor} hover:bg-slate-800/50`}
                        >
                            {showLineNumbers && (
                                <span className="px-3 py-1 text-slate-500 select-none min-w-[60px] text-right">
                                    {!part.added && !part.removed ? lineNumber : ''}
                                </span>
                            )}
                            <span className="px-2 py-1 text-slate-500 select-none">{prefix}</span>
                            <pre className={`flex-1 py-1 pr-4 ${textColor} overflow-x-auto`}>
                                <code>{line || ' '}</code>
                            </pre>
                        </div>
                    );
                });
            })}
        </div>
    );
}

// Split Diff View
function SplitDiff({
    original,
    modified,
    showLineNumbers,
}: {
    original: string;
    modified: string;
    showLineNumbers: boolean;
}) {
    const originalLines = original.split('\n');
    const modifiedLines = modified.split('\n');
    const maxLines = Math.max(originalLines.length, modifiedLines.length);

    return (
        <div className="grid grid-cols-2 divide-x divide-slate-700 font-mono text-sm">
            {/* Original (Left) */}
            <div>
                <div className="bg-slate-800 px-4 py-1 text-xs text-slate-400 border-b border-slate-700">
                    Original
                </div>
                <div>
                    {originalLines.map((line, idx) => (
                        <div
                            key={`orig-${idx}`}
                            className="flex items-start hover:bg-slate-800/50"
                        >
                            {showLineNumbers && (
                                <span className="px-3 py-1 text-slate-500 select-none min-w-[50px] text-right">
                                    {idx + 1}
                                </span>
                            )}
                            <pre className="flex-1 py-1 pr-4 text-slate-300 overflow-x-auto">
                                <code>{line || ' '}</code>
                            </pre>
                        </div>
                    ))}
                </div>
            </div>

            {/* Modified (Right) */}
            <div>
                <div className="bg-slate-800 px-4 py-1 text-xs text-slate-400 border-b border-slate-700">
                    Modified
                </div>
                <div>
                    {modifiedLines.map((line, idx) => (
                        <div
                            key={`mod-${idx}`}
                            className="flex items-start hover:bg-slate-800/50"
                        >
                            {showLineNumbers && (
                                <span className="px-3 py-1 text-slate-500 select-none min-w-[50px] text-right">
                                    {idx + 1}
                                </span>
                            )}
                            <pre className="flex-1 py-1 pr-4 text-slate-300 overflow-x-auto">
                                <code>{line || ' '}</code>
                            </pre>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
