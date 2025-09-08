'use client';

import DocumentList from '@/components/document/DocumentList';
import DocumentPreview from '@/components/document/DocumentPreview';
import { Filter, Search } from 'lucide-react';
import { useEffect, useState } from 'react';

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

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [previewDocument, setPreviewDocument] = useState<Document | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);

    // 임시 데이터 로드
    useEffect(() => {
        const loadDocuments = async () => {
            setIsLoading(true);
            try {
                // TODO: 실제 API 호출로 대체
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
            } catch (error) {
                console.error('Failed to load documents:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadDocuments();
    }, []);

    const handleUpload = async (files: File[]) => {
        console.log('Uploading files:', files);
        // TODO: 실제 업로드 로직 구현
        // 1. 파일을 MinIO에 업로드
        // 2. 문서 처리 작업 시작
        // 3. SSE를 통해 실시간 상태 업데이트
    };

    const handleRemove = (fileId: string) => {
        console.log('Removing file:', fileId);
        // TODO: 업로드 대기열에서 파일 제거
    };

    const handleDownload = async (documentId: string) => {
        console.log('Downloading document:', documentId);
        // TODO: 실제 다운로드 로직 구현
    };

    const handleDelete = async (documentId: string) => {
        console.log('Deleting document:', documentId);
        // TODO: 실제 삭제 로직 구현
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    };

    const handleRetry = async (documentId: string) => {
        console.log('Retrying document processing:', documentId);
        // TODO: 실제 재시도 로직 구현
    };

    const handlePreview = (document: Document) => {
        setPreviewDocument(document);
        setIsPreviewOpen(true);
    };

    const filteredDocuments = documents.filter(doc => {
        const matchesSearch = doc.original_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const getStatusCounts = () => {
        const counts = {
            all: documents.length,
            pending: documents.filter(d => d.status === 'pending').length,
            processing: documents.filter(d => d.status === 'processing').length,
            completed: documents.filter(d => d.status === 'completed').length,
            failed: documents.filter(d => d.status === 'failed').length
        };
        return counts;
    };

    const statusCounts = getStatusCounts();

    return (
        <div className="h-full flex flex-col">
            {/* 헤더 */}
            <div className="bg-white border-b border-gray-200 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">문서 관리</h1>
                        <p className="text-gray-600 mt-1">문서를 업로드하고 관리하세요</p>
                    </div>
                </div>
            </div>

            {/* 필터 및 검색 */}
            <div className="bg-white border-b border-gray-200 p-4">
                <div className="flex items-center space-x-4">
                    {/* 검색 */}
                    <div className="flex-1 max-w-md">
                        <div className="relative">
                            <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                placeholder="문서 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* 상태 필터 */}
                    <div className="flex items-center space-x-2">
                        <Filter size={16} className="text-gray-400" />
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">전체 ({statusCounts.all})</option>
                            <option value="pending">대기중 ({statusCounts.pending})</option>
                            <option value="processing">처리중 ({statusCounts.processing})</option>
                            <option value="completed">완료 ({statusCounts.completed})</option>
                            <option value="failed">실패 ({statusCounts.failed})</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* 메인 컨텐츠 */}
            <div className="flex-1 overflow-hidden">
                <div className="h-full p-6 overflow-y-auto">
                    <DocumentList
                        documents={filteredDocuments}
                        onDownload={handleDownload}
                        onDelete={handleDelete}
                        onRetry={handleRetry}
                        onPreview={handlePreview}
                        isLoading={isLoading}
                    />
                </div>
            </div>

            {/* 문서 미리보기 모달 */}
            <DocumentPreview
                document={previewDocument}
                isOpen={isPreviewOpen}
                onClose={() => {
                    setIsPreviewOpen(false);
                    setPreviewDocument(null);
                }}
                onDownload={handleDownload}
            />
        </div>
    );
}
