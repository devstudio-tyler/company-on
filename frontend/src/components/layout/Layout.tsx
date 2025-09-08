'use client';

import { getClientId } from '@/lib/utils';
import { ChatSession } from '@/types';
import dynamic from 'next/dynamic';
import React, { memo, useEffect, useState } from 'react';

// Header와 Sidebar들을 동적으로 로드
const Header = dynamic(() => import('./Header'));
const SessionSidebar = dynamic(() => import('./Sidebar').then(mod => ({ default: mod.SessionSidebar })));
const DocumentSidebar = dynamic(() => import('./DocumentSidebar'));
const GlobalDragDrop = dynamic(() => import('../GlobalDragDrop'));

interface Document {
    id: string;
    filename: string;
    original_name: string;
    file_size: number;
    mime_type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    upload_session_id: string;
    created_at: string;
    updated_at: string;
    processing_progress?: number;
    error_message?: string;
    chunk_count?: number;
    embedding_count?: number;
}

interface LayoutProps {
    children: React.ReactNode;
    className?: string;
}

// Layout 컴포넌트를 memo로 최적화
const Layout = memo(function Layout({ children, className = '' }: LayoutProps) {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [sidebarMode, setSidebarMode] = useState<'session' | 'document' | 'closed'>('session');
    const [isLoading, setIsLoading] = useState(true);

    // 클라이언트 ID 초기화
    useEffect(() => {
        const clientId = getClientId();
        console.log('Client ID:', clientId);
    }, []);

    // 세션 목록 로드 (임시 데이터)
    useEffect(() => {
        // TODO: 실제 API 호출로 대체
        const mockSessions: ChatSession[] = [
            {
                id: '1',
                title: '회사 정책 문의',
                description: '휴가 정책과 복리후생에 대한 질문',
                client_id: getClientId(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                message_count: 5,
                is_pinned: true,
                tags: ['정책', '휴가']
            },
            {
                id: '2',
                title: '프로젝트 관련 질문',
                description: '새로운 프로젝트 진행 방식에 대한 문의',
                client_id: getClientId(),
                created_at: new Date(Date.now() - 86400000).toISOString(),
                updated_at: new Date(Date.now() - 3600000).toISOString(),
                message_count: 12,
                is_pinned: false,
                tags: ['프로젝트', '업무']
            },
            {
                id: '3',
                title: '기술 문서 검토',
                description: 'API 문서와 기술 스펙 검토',
                client_id: getClientId(),
                created_at: new Date(Date.now() - 172800000).toISOString(),
                updated_at: new Date(Date.now() - 7200000).toISOString(),
                message_count: 8,
                is_pinned: false,
                tags: ['기술', 'API']
            }
        ];

        setSessions(mockSessions);
        setIsLoading(false);
    }, []);

    // 문서 목록 로드 (임시 데이터)
    useEffect(() => {
        const mockDocuments: Document[] = [
            {
                id: '1',
                filename: 'company-policy.pdf',
                original_name: '회사 정책서.pdf',
                file_size: 2048576,
                mime_type: 'application/pdf',
                status: 'completed',
                upload_session_id: 'session-1',
                created_at: new Date(Date.now() - 86400000).toISOString(),
                updated_at: new Date(Date.now() - 3600000).toISOString(),
                chunk_count: 15,
                embedding_count: 15
            },
            {
                id: '2',
                filename: 'project-guide.docx',
                original_name: '프로젝트 가이드.docx',
                file_size: 1536000,
                mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                status: 'processing',
                upload_session_id: 'session-2',
                created_at: new Date(Date.now() - 7200000).toISOString(),
                updated_at: new Date(Date.now() - 1800000).toISOString(),
                processing_progress: 65
            },
            {
                id: '3',
                filename: 'meeting-notes.txt',
                original_name: '회의록.txt',
                file_size: 512000,
                mime_type: 'text/plain',
                status: 'failed',
                upload_session_id: 'session-3',
                created_at: new Date(Date.now() - 14400000).toISOString(),
                updated_at: new Date(Date.now() - 900000).toISOString(),
                error_message: '파일 형식을 인식할 수 없습니다.'
            },
            {
                id: '4',
                filename: 'technical-spec.pdf',
                original_name: '기술 명세서.pdf',
                file_size: 5120000,
                mime_type: 'application/pdf',
                status: 'pending',
                upload_session_id: 'session-4',
                created_at: new Date(Date.now() - 300000).toISOString(),
                updated_at: new Date(Date.now() - 300000).toISOString()
            }
        ];

        setDocuments(mockDocuments);
    }, []);

    const currentSession = sessions.find(session => session.id === currentSessionId);

    const handleSessionSelect = (sessionId: string) => {
        setCurrentSessionId(sessionId);
    };

    const handleNewSession = () => {
        // TODO: 새 세션 생성 로직
        console.log('새 세션 생성');
    };

    const handleSearch = (query: string) => {
        // TODO: 검색 로직
        console.log('검색:', query);
    };

    const handleSessionUpdate = (session: ChatSession) => {
        setSessions(prev => {
            const existingIndex = prev.findIndex(s => s.id === session.id);
            if (existingIndex >= 0) {
                // 기존 세션 업데이트
                const updated = [...prev];
                updated[existingIndex] = session;
                return updated;
            } else {
                // 새 세션 추가
                return [session, ...prev];
            }
        });
    };

    const handleSessionDelete = (sessionId: string) => {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (currentSessionId === sessionId) {
            setCurrentSessionId(undefined);
        }
    };

    const handleMenuToggle = () => {
        setSidebarOpen(!sidebarOpen);
    };

    const handleUpload = () => {
        // TODO: 문서 업로드 모달 열기 또는 문서 관리 페이지로 이동
        window.location.href = '/documents';
    };

    const handleGlobalFileDrop = (files: File[]) => {
        console.log('전역 파일 드롭:', files);
        // TODO: 실제 파일 업로드 로직 구현
        // 1. 파일을 MinIO에 업로드
        // 2. 문서 처리 작업 시작
        // 3. SSE를 통해 실시간 상태 업데이트
    };

    const handleDocumentDownload = (documentId: string) => {
        console.log('문서 다운로드:', documentId);
    };

    const handleDocumentDelete = (documentId: string) => {
        console.log('문서 삭제:', documentId);
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    };

    const handleDocumentRetry = (documentId: string) => {
        console.log('문서 재시도:', documentId);
    };

    const handleDocumentPreview = (document: Document) => {
        console.log('문서 미리보기:', document);
    };

    const handleModeChange = (mode: 'session' | 'document') => {
        setSidebarMode(mode);
        setSidebarOpen(true);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <GlobalDragDrop onFileDrop={handleGlobalFileDrop}>
            <div className={`flex h-screen bg-gray-50 ${className}`}>
                {/* 사이드바 */}
                <div className={`${sidebarOpen ? 'block' : 'hidden'}`}>
                    {sidebarMode === 'session' && (
                        <SessionSidebar
                            sessions={sessions}
                            currentSessionId={currentSessionId}
                            onSessionSelect={handleSessionSelect}
                            onNewSession={handleNewSession}
                            onSearch={handleSearch}
                            onSessionUpdate={handleSessionUpdate}
                            onSessionDelete={handleSessionDelete}
                            onModeChange={handleModeChange}
                            currentMode={sidebarMode}
                        />
                    )}
                    {sidebarMode === 'document' && (
                        <DocumentSidebar
                            documents={documents}
                            onUpload={handleGlobalFileDrop}
                            onDownload={handleDocumentDownload}
                            onDelete={handleDocumentDelete}
                            onRetry={handleDocumentRetry}
                            onPreview={handleDocumentPreview}
                            onModeChange={handleModeChange}
                            currentMode={sidebarMode}
                        />
                    )}
                </div>

                {/* 메인 컨텐츠 */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* 헤더 */}
                    <Header
                        currentSession={currentSession}
                        onSearch={handleSearch}
                        onMenuToggle={handleMenuToggle}
                        onUpload={handleUpload}
                    />

                    {/* 컨텐츠 영역 */}
                    <main className="flex-1 overflow-hidden">
                        {children}
                    </main>
                </div>

                {/* 모바일 오버레이 */}
                {sidebarOpen && (
                    <div
                        className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
                        onClick={() => setSidebarOpen(false)}
                    />
                )}
            </div>
        </GlobalDragDrop>
    );
});

export default Layout;
