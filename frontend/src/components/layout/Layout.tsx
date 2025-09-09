'use client';

import { getClientId } from '@/lib/utils';
import { ChatSession } from '@/types';
import dynamic from 'next/dynamic';
import React, { memo, useCallback, useEffect, useState } from 'react';
import DocumentPreviewModal from '../DocumentPreviewModal';
import DocumentSidebar from './DocumentSidebar';

// Header와 Sidebar들을 동적으로 로드
const Header = dynamic(() => import('./Header'), { ssr: false });
const SessionSidebar = dynamic(() => import('./Sidebar').then(mod => ({ default: mod.SessionSidebar })), { ssr: false });
const GlobalDragDrop = dynamic(() => import('../GlobalDragDrop'), { ssr: false });

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
    const [isUploading, setIsUploading] = useState(false);
    const [activeUploads, setActiveUploads] = useState<Map<string, string>>(new Map()); // uploadId -> documentId
    const [pollingActive, setPollingActive] = useState(false);
    const [isDocumentsLoading, setIsDocumentsLoading] = useState(false);
    const [isInitialDocumentsLoad, setIsInitialDocumentsLoad] = useState(true);
    const [previewModal, setPreviewModal] = useState<{ isOpen: boolean; documentId: string; filename: string }>({
        isOpen: false,
        documentId: '',
        filename: ''
    });

    async function fetchDocuments(isInitial = false) {
        try {
            if (isInitial) {
                setIsDocumentsLoading(true);
            }
            console.log('Fetching documents from: /api/v1/documents');
            const res = await fetch('/api/v1/documents');
            console.log('Response status:', res.status);
            console.log('Response headers:', Object.fromEntries(res.headers.entries()));

            if (!res.ok) {
                const errorText = await res.text();
                console.error('Response error text:', errorText);
                throw new Error(`문서 목록 조회 실패: ${res.status} - ${errorText}`);
            }

            const data = await res.json();
            console.log('Response data:', data);

            const docs = (data?.documents || []).map((d: any) => ({
                id: String(d.id),
                filename: d.filename,
                original_name: d.title ?? d.filename,
                file_size: d.file_size,
                mime_type: d.content_type || 'application/octet-stream',
                status: d.status,
                upload_session_id: d.upload_session_id || '',
                created_at: d.created_at,
                updated_at: d.updated_at
            })) as Document[];
            setDocuments(docs);
        } catch (e) {
            console.error('Fetch documents error:', e);
            console.error('Error details:', {
                name: (e as Error).name,
                message: (e as Error).message,
                stack: (e as Error).stack
            });
        } finally {
            setIsLoading(false);
            if (isInitial) {
                setIsDocumentsLoading(false);
                setIsInitialDocumentsLoad(false);
            }
        }
    }

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

    // 문서 목록 로드 (실제 API)
    useEffect(() => {
        fetchDocuments(true); // 초기 로딩으로 표시
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 폴링 로직 - processing 상태 문서가 있을 때만 활성화
    useEffect(() => {
        if (!pollingActive) return;

        const pollInterval = setInterval(() => {
            fetchDocuments().then(() => {
                setDocuments(current => {
                    const hasProcessing = current.some(doc => doc.status === 'processing');
                    if (!hasProcessing) {
                        setPollingActive(false);
                    }
                    return current;
                });
            });
        }, 3000);

        return () => clearInterval(pollInterval);
    }, [pollingActive]);

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
        // 파일 선택 다이얼로그 열기
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '.pdf,.docx,.xlsx,.csv,.png,.jpg,.jpeg';
        input.onchange = (e) => {
            const files = Array.from((e.target as HTMLInputElement).files || []);
            if (files.length > 0) {
                handleGlobalFileDrop(files);
            }
        };
        input.click();
    };

    const validateFileType = (file: File): boolean => {
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'image/png',
            'image/jpeg'
        ];

        const allowedExtensions = ['.pdf', '.docx', '.xlsx', '.csv', '.png', '.jpg', '.jpeg'];

        const isValidType = allowedTypes.includes(file.type.toLowerCase());
        const isValidExtension = allowedExtensions.some(ext =>
            file.name.toLowerCase().endsWith(ext)
        );

        return isValidType || isValidExtension;
    };

    const handleGlobalFileDrop = async (files: File[]) => {
        if (!files || files.length === 0) return;

        // 파일 타입 검증
        const validFiles: File[] = [];
        const invalidFiles: string[] = [];

        files.forEach(file => {
            if (validateFileType(file)) {
                validFiles.push(file);
            } else {
                invalidFiles.push(file.name);
            }
        });

        if (invalidFiles.length > 0) {
            alert(`지원되지 않는 파일 형식입니다:\n${invalidFiles.join('\n')}\n\n지원 형식: PDF, DOCX, XLSX, CSV, PNG, JPG`);
        }

        if (validFiles.length === 0) return;

        setIsUploading(true);
        try {
            for (const file of validFiles) {
                // 직접 업로드 (CORS 문제 우회)
                const formData = new FormData();
                formData.append('file', file);
                formData.append('metadata', JSON.stringify({}));

                const uploadRes = await fetch('/api/v1/documents/upload-direct', {
                    method: 'POST',
                    body: formData
                });

                if (!uploadRes.ok) {
                    const errorText = await uploadRes.text();
                    throw new Error(`업로드 실패: ${uploadRes.status} - ${errorText}`);
                }

                const uploadData = await uploadRes.json();
                const documentId = uploadData.document_id;

                // 임시 문서를 목록에 추가 (processing 상태)
                const tempDocument: Document = {
                    id: String(documentId),
                    filename: file.name,
                    original_name: file.name,
                    file_size: file.size,
                    mime_type: file.type || 'application/octet-stream',
                    status: 'processing',
                    upload_session_id: '', // 임시로 빈 문자열
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    processing_progress: 0
                };

                setDocuments(prev => [tempDocument, ...prev]);

                // 폴링 시작 (아직 활성화되지 않은 경우에만)
                if (!pollingActive) {
                    setPollingActive(true);
                }

                // 문서 사이드바가 보이도록 전환
                setSidebarMode('document');
                setSidebarOpen(true);

                console.log('업로드 완료, 처리 시작됨. document_id=', documentId);
            }
        } catch (e) {
            console.error(e);
            alert(`파일 업로드 중 오류가 발생했습니다: ${e}`);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDocumentDownload = useCallback(async (documentId: string) => {
        try {
            // 백엔드에서 307 리다이렉트로 처리하므로 직접 URL로 이동
            window.location.href = `/api/v1/documents/${documentId}/download`;
        } catch (error) {
            console.error('다운로드 오류:', error);
            alert('다운로드 중 오류가 발생했습니다.');
        }
    }, []);

    const handleDocumentDelete = useCallback(async (documentId: string) => {
        if (!confirm('정말로 이 문서를 삭제하시겠습니까?')) return;

        try {
            const response = await fetch(`/api/v1/documents/${documentId}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error(`삭제 실패: ${response.status}`);

            setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        } catch (error) {
            console.error('삭제 오류:', error);
            alert('삭제 중 오류가 발생했습니다.');
        }
    }, []);

    const handleDocumentRetry = useCallback(async (documentId: string) => {
        try {
            const response = await fetch(`/api/v1/documents/${documentId}/retry`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error(`재시도 실패: ${response.status}`);

            // 문서 상태를 processing으로 업데이트
            setDocuments(prev => prev.map(doc =>
                doc.id === documentId
                    ? { ...doc, status: 'processing' as const, error_message: undefined }
                    : doc
            ));
        } catch (error) {
            console.error('재시도 오류:', error);
            alert('재시도 중 오류가 발생했습니다.');
        }
    }, []);

    const handleDocumentPreview = useCallback((document: Document) => {
        setPreviewModal({
            isOpen: true,
            documentId: document.id,
            filename: document.filename
        });
    }, []);

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
                            isLoading={isDocumentsLoading}
                            isInitialLoad={isInitialDocumentsLoad}
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
                    {isUploading && (
                        <div className="px-4 py-2 text-sm text-gray-600">파일 업로드 중...</div>
                    )}

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

                {/* 문서 프리뷰 모달 */}
                <DocumentPreviewModal
                    isOpen={previewModal.isOpen}
                    onClose={() => setPreviewModal({ isOpen: false, documentId: '', filename: '' })}
                    documentId={previewModal.documentId}
                    filename={previewModal.filename}
                />
            </div>
        </GlobalDragDrop>
    );
});

export default Layout;
