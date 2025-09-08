'use client';

import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
    AlertCircle,
    CheckCircle,
    Clock,
    Download,
    Eye,
    FileText,
    RefreshCw,
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

interface DocumentListProps {
    documents: Document[];
    onDownload: (documentId: string) => void;
    onDelete: (documentId: string) => void;
    onRetry: (documentId: string) => void;
    onPreview: (document: Document) => void;
    isLoading?: boolean;
}

const DocumentList = memo(function DocumentList({
    documents,
    onDownload,
    onDelete,
    onRetry,
    onPreview,
    isLoading = false
}: DocumentListProps) {
    const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);

    const getStatusIcon = (status: Document['status']) => {
        switch (status) {
            case 'pending':
                return <Clock size={16} className="text-yellow-500" />;
            case 'processing':
                return <RefreshCw size={16} className="text-blue-500 animate-spin" />;
            case 'completed':
                return <CheckCircle size={16} className="text-green-500" />;
            case 'failed':
                return <AlertCircle size={16} className="text-red-500" />;
            default:
                return <Clock size={16} className="text-gray-500" />;
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

    const handleSelectDocument = (documentId: string) => {
        setSelectedDocuments(prev =>
            prev.includes(documentId)
                ? prev.filter(id => id !== documentId)
                : [...prev, documentId]
        );
    };

    const handleSelectAll = () => {
        if (selectedDocuments.length === documents.length) {
            setSelectedDocuments([]);
        } else {
            setSelectedDocuments(documents.map(doc => doc.id));
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                        <div className="bg-gray-200 rounded-lg h-20"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (documents.length === 0) {
        return (
            <div className="text-center py-12">
                <FileText size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">문서가 없습니다</h3>
                <p className="text-gray-500">새로운 문서를 업로드해보세요.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* 헤더 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <h2 className="text-lg font-semibold text-gray-900">
                        문서 목록 ({documents.length})
                    </h2>
                    {documents.length > 0 && (
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={selectedDocuments.length === documents.length}
                                onChange={handleSelectAll}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="ml-2 text-sm text-gray-700">전체 선택</span>
                        </label>
                    )}
                </div>

                {selectedDocuments.length > 0 && (
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-500">
                            {selectedDocuments.length}개 선택됨
                        </span>
                        <button className="text-sm text-red-600 hover:text-red-800">
                            선택 삭제
                        </button>
                    </div>
                )}
            </div>

            {/* 문서 목록 */}
            <div className="space-y-2">
                {documents.map((document) => (
                    <div
                        key={document.id}
                        className={`
                            bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow
                            ${selectedDocuments.includes(document.id) ? 'ring-2 ring-blue-500' : ''}
                        `}
                    >
                        <div className="flex items-start space-x-4">
                            {/* 체크박스 */}
                            <input
                                type="checkbox"
                                checked={selectedDocuments.includes(document.id)}
                                onChange={() => handleSelectDocument(document.id)}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
                            />

                            {/* 파일 아이콘 */}
                            <div className="flex-shrink-0">
                                <span className="text-2xl">
                                    {getFileIcon(document.mime_type)}
                                </span>
                            </div>

                            {/* 문서 정보 */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-sm font-medium text-gray-900 truncate">
                                            {document.original_name}
                                        </h3>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {formatFileSize(document.file_size)} •
                                            {formatDistanceToNow(new Date(document.created_at), {
                                                addSuffix: true,
                                                locale: ko
                                            })}
                                        </p>
                                    </div>

                                    {/* 상태 */}
                                    <div className="flex items-center space-x-2 ml-4">
                                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                                            {getStatusIcon(document.status)}
                                            <span className="ml-1">{getStatusText(document.status)}</span>
                                        </div>

                                        {/* 진행률 */}
                                        {document.status === 'processing' && document.processing_progress !== undefined && (
                                            <div className="flex items-center space-x-2">
                                                <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
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
                                </div>

                                {/* 에러 메시지 */}
                                {document.status === 'failed' && document.error_message && (
                                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                                        {document.error_message}
                                    </div>
                                )}

                                {/* 처리 정보 */}
                                {document.status === 'completed' && (
                                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                                        {document.chunk_count && (
                                            <span>청크: {document.chunk_count}개</span>
                                        )}
                                        {document.embedding_count && (
                                            <span>임베딩: {document.embedding_count}개</span>
                                        )}
                                    </div>
                                )}

                                {/* 액션 버튼들 */}
                                <div className="mt-3 flex items-center space-x-2">
                                    <button
                                        onClick={() => onPreview(document)}
                                        className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                                    >
                                        <Eye size={12} className="mr-1" />
                                        미리보기
                                    </button>

                                    <button
                                        onClick={() => onDownload(document.id)}
                                        className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                                    >
                                        <Download size={12} className="mr-1" />
                                        다운로드
                                    </button>

                                    {document.status === 'failed' && (
                                        <button
                                            onClick={() => onRetry(document.id)}
                                            className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                                        >
                                            <RefreshCw size={12} className="mr-1" />
                                            재시도
                                        </button>
                                    )}

                                    <button
                                        onClick={() => onDelete(document.id)}
                                        className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                                    >
                                        <Trash2 size={12} className="mr-1" />
                                        삭제
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
});

export default DocumentList;

