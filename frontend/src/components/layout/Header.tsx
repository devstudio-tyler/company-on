'use client';

import { ChatSession } from '@/types';
import { Menu, MessageSquare, Upload } from 'lucide-react';
import React, { useState } from 'react';

interface HeaderProps {
    currentSession?: ChatSession;
    onSearch: (query: string) => void;
    onMenuToggle: () => void;
    onUpload?: () => void;
    className?: string;
}

export default function Header({
    currentSession,
    onSearch,
    onMenuToggle,
    onUpload,
    className = ''
}: HeaderProps) {
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(searchQuery);
    };

    return (
        <header className={`bg-white border-b border-gray-200 px-4 py-3 ${className}`}>
            <div className="flex items-center justify-between h-full">
                {/* 왼쪽: 드로우바 토글 + 현재 세션 정보 */}
                <div className="flex items-center gap-4">
                    {/* 드로우바 토글 버튼 */}
                    <button
                        onClick={onMenuToggle}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    {currentSession ? (
                        <div className="flex items-center gap-3">
                            <MessageSquare className="w-5 h-5 text-blue-600" />
                            <div>
                                <h1 className="font-semibold text-gray-900">{currentSession.title}</h1>
                                {currentSession.description && (
                                    <p className="text-sm text-gray-500">{currentSession.description}</p>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            <h1 className="font-semibold text-gray-900">Company-on</h1>
                        </div>
                    )}
                </div>

                {/* 오른쪽: 업로드만 남김 */}
                <div className="flex items-center gap-2">
                    {onUpload && (
                        <button
                            onClick={onUpload}
                            className="inline-flex items-center h-8 px-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        >
                            <Upload size={16} className="mr-2" />
                            업로드
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
}
