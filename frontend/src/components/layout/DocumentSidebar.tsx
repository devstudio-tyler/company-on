'use client';

import {
    AlertCircle,
    CheckCircle,
    Clock,
    Download,
    Eye,
    FileText,
    Filter,
    RefreshCw,
    Search,
    Trash2
} from 'lucide-react';
import { memo, useState } from 'react';

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

interface DocumentSidebarProps {
    documents: Document[];
    onUpload: (files: File[]) => void;
    onDownload: (documentId: string) => void;
    onDelete: (documentId: string) => void;
    onRetry: (documentId: string) => void;
    onPreview: (document: Document) => void;
    onModeChange?: (mode: 'session' | 'document') => void;
    currentMode?: 'session' | 'document';
    className?: string;
    isLoading?: boolean;
    isInitialLoad?: boolean;
}

const DocumentSidebar = memo(function DocumentSidebar({
    documents,
    onUpload,
    onDownload,
    onDelete,
    onRetry,
    onPreview,
    onModeChange,
    currentMode = 'document',
    className = '',
    isLoading = false,
    isInitialLoad = false
}: DocumentSidebarProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');

    const getStatusIcon = (status: Document['status']) => {
        switch (status) {
            case 'pending':
                return <Clock size={14} className="text-yellow-500" />;
            case 'processing':
                return <RefreshCw size={14} className="text-blue-500 animate-spin" />;
            case 'completed':
                return <CheckCircle size={14} className="text-green-500" />;
            case 'failed':
                return <AlertCircle size={14} className="text-red-500" />;
            default:
                return <Clock size={14} className="text-gray-500" />;
        }
    };

    const getStatusText = (status: Document['status']) => {
        switch (status) {
            case 'pending':
                return '대기중';
            case 'processing':
                return '처리중';
            case 'completed':
                return '완료';
            case 'failed':
                return '실패';
            default:
                return '알 수 없음';
        }
    };

    const getStatusColor = (status: Document['status']) => {
        switch (status) {
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'processing':
                return 'bg-blue-100 text-blue-800';
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getFileIcon = (mimeType: string) => {
        if (mimeType.includes('pdf')) return '📄';
        if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
        if (mimeType.includes('text')) return '📄';
        return '📄';
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
        <div className={`bg-white border-r border-gray-200 flex flex-col h-full w-80 ${className}`}>
            {/* 헤더 - 모드 선택 (닫기 버튼 제거, 헤더 햄버거로 제어) */}
            <div className="border-b border-gray-200 px-3 py-3">
                <div className="flex items-center justify-between">
                    {onModeChange ? (
                        <div className="flex items-center bg-gray-100 rounded-lg p-1 flex-1 h-9">
                            <button
                                onClick={() => onModeChange('session')}
                                className={`flex-1 h-full px-3 text-sm rounded-md transition-colors flex items-center justify-center ${currentMode === 'session'
                                    ? 'bg-white text-blue-600 shadow-sm'
                                    : 'text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                세션
                            </button>
                            <button
                                onClick={() => onModeChange('document')}
                                className={`flex-1 h-full px-3 text-sm rounded-md transition-colors flex items-center justify-center ${currentMode === 'document'
                                    ? 'bg-white text-blue-600 shadow-sm'
                                    : 'text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                문서
                            </button>
                        </div>
                    ) : (
                        <h1 className="text-xl font-bold text-gray-900">문서 관리</h1>
                    )}
                </div>
            </div>

            {/* 검색 및 필터 */}
            <div className="p-3 border-b border-gray-200">
                <div className="space-y-3">
                    {/* 검색 */}
                    <div className="relative">
                        <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="문서 검색..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    {/* 상태 필터 */}
                    <div className="flex items-center space-x-2">
                        <Filter size={14} className="text-gray-400" />
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
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


            {/* 문서 목록 */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-2">
                    {isLoading && isInitialLoad ? (
                        <div className="text-center text-gray-500 py-8">
                            <RefreshCw size={32} className="mx-auto mb-2 text-gray-400 animate-spin" />
                            <div className="text-sm">문서를 불러오는 중...</div>
                            <div className="text-xs text-gray-400 mt-1">
                                잠시만 기다려주세요
                            </div>
                        </div>
                    ) : filteredDocuments.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <FileText size={32} className="mx-auto mb-2 text-gray-400" />
                            <div className="text-sm">문서가 없습니다</div>
                            <div className="text-xs text-gray-400 mt-1">
                                새 문서를 업로드해보세요
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {filteredDocuments
                                .sort((a, b) => {
                                    // 상태별 정렬 (처리중 > 대기중 > 완료 > 실패)
                                    const statusOrder = { processing: 0, pending: 1, completed: 2, failed: 3 };
                                    const aOrder = statusOrder[a.status as keyof typeof statusOrder] ?? 4;
                                    const bOrder = statusOrder[b.status as keyof typeof statusOrder] ?? 4;
                                    if (aOrder !== bOrder) return aOrder - bOrder;
                                    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
                                })
                                .map((document) => (
                                    <div
                                        key={document.id}
                                        className="group relative p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all"
                                    >
                                        {/* 문서 정보 */}
                                        <div className="flex items-start space-x-3">
                                            <span className="text-lg flex-shrink-0">
                                                {getFileIcon(document.mime_type)}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="text-sm font-medium text-gray-900 truncate">
                                                    {document.original_name}
                                                </h3>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    {formatFileSize(document.file_size)}
                                                </p>

                                                {/* 상태 */}
                                                <div className="flex items-center justify-between mt-2">
                                                    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                                                        {getStatusIcon(document.status)}
                                                        <span className="ml-1">{getStatusText(document.status)}</span>
                                                    </div>

                                                    {/* 진행률 */}
                                                    {document.status === 'processing' && document.processing_progress !== undefined && (
                                                        <div className="flex items-center space-x-1">
                                                            <div className="w-12 h-1 bg-gray-200 rounded-full overflow-hidden">
                                                                <div
                                                                    className="h-full bg-blue-500 transition-all duration-300"
                                                                    style={{ width: `${document.processing_progress}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-xs text-gray-500">
                                                                {document.processing_progress}%
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* 에러 메시지 */}
                                                {document.status === 'failed' && document.error_message && (
                                                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                                                        {document.error_message}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* 액션 버튼들 (호버 시 표시) */}
                                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                                            <button
                                                onClick={() => onPreview(document)}
                                                className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded"
                                                title="미리보기"
                                            >
                                                <Eye size={12} />
                                            </button>

                                            <button
                                                onClick={() => onDownload(document.id)}
                                                className="p-1 text-gray-400 hover:text-green-500 hover:bg-green-50 rounded"
                                                title="다운로드"
                                            >
                                                <Download size={12} />
                                            </button>

                                            {document.status === 'failed' && (
                                                <button
                                                    onClick={() => onRetry(document.id)}
                                                    className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded"
                                                    title="재시도"
                                                >
                                                    <RefreshCw size={12} />
                                                </button>
                                            )}

                                            <button
                                                onClick={() => onDelete(document.id)}
                                                className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                                                title="삭제"
                                            >
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 하단 링크 */}
        </div>
    );
});

export default DocumentSidebar;
