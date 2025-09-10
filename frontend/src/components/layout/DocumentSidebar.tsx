'use client';

import {
    AlertCircle,
    CheckCircle,
    Clock,
    Download,
    Eye,
    FileText,
    Filter,
    Image,
    RefreshCw,
    Search,
    Table,
    Trash2,
    X
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
    failure_type?: 'upload_failed' | 'processing_failed';
    retryable?: boolean;
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
    hasError?: boolean;
    onRefresh?: () => void;
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
    isInitialLoad = false,
    hasError = false,
    onRefresh
}: DocumentSidebarProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [typeFilters, setTypeFilters] = useState<string[]>([]);

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

    // 문서 타입 결정 함수 (허용 확장자: PDF, DOCX, XLSX, CSV, PNG, JPG)
    const getDocumentType = (mimeType: string, filename: string) => {
        const ext = filename.toLowerCase().split('.').pop();
        const lowerMimeType = mimeType.toLowerCase();

        // 확장자 우선 검사 (더 정확함)
        if (ext === 'pdf') return 'pdf';
        if (ext === 'docx') return 'word';
        if (ext === 'xlsx' || ext === 'csv') return 'table';
        if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') return 'image';

        // MIME 타입 검사 (확장자가 없는 경우를 대비)
        if (lowerMimeType.includes('pdf')) return 'pdf';

        // Word 문서 (wordprocessingml.document만)
        if (lowerMimeType.includes('wordprocessingml.document') ||
            lowerMimeType.includes('application/msword')) return 'word';

        // Excel/스프레드시트 (spreadsheetml.sheet 또는 excel)
        if (lowerMimeType.includes('spreadsheetml.sheet') ||
            lowerMimeType.includes('excel') ||
            lowerMimeType.includes('csv')) return 'table';

        // 이미지
        if (lowerMimeType.includes('image/')) return 'image';

        // 기타는 모두 other로 분류
        return 'other';
    };

    // 타입별 아이콘과 라벨 (허용 확장자에 맞게 수정)
    const getTypeInfo = (type: string) => {
        switch (type) {
            case 'pdf':
                return { icon: <FileText size={12} />, label: 'PDF', color: 'bg-red-100 text-red-700 border-red-200' };
            case 'word':
                return { icon: <FileText size={12} />, label: 'Word', color: 'bg-blue-100 text-blue-700 border-blue-200' };
            case 'table':
                return { icon: <Table size={12} />, label: 'Table', color: 'bg-green-100 text-green-700 border-green-200' };
            case 'image':
                return { icon: <Image size={12} />, label: 'Image', color: 'bg-purple-100 text-purple-700 border-purple-200' };
            default:
                return { icon: <FileText size={12} />, label: '기타', color: 'bg-gray-100 text-gray-700 border-gray-200' };
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // 한글 검색을 위한 정규화 함수
    const normalizeText = (text: string) => {
        return text
            .normalize('NFC') // 유니코드 정규화
            .toLowerCase()
            .replace(/[\s\u00A0\u2000-\u200B\u2028\u2029\u3000]/g, ''); // 공백 제거
    };

    // 한글 자모 분리 검색을 위한 함수
    const searchInText = (text: string, query: string) => {
        const normalizedText = normalizeText(text);
        const normalizedQuery = normalizeText(query);

        // 기본 검색
        if (normalizedText.includes(normalizedQuery)) {
            return true;
        }

        // 한글 자모 분리 검색 (초성 검색)
        const hangulRegex = /[가-힣]/;
        if (hangulRegex.test(normalizedQuery)) {
            // 한글 자모 분리 함수
            const decomposeHangul = (str: string) => {
                return str.split('').map(char => {
                    const code = char.charCodeAt(0);
                    if (code >= 0xAC00 && code <= 0xD7A3) {
                        const base = code - 0xAC00;
                        const cho = Math.floor(base / 588);
                        const jung = Math.floor((base % 588) / 28);
                        const jong = base % 28;
                        return String.fromCharCode(0x1100 + cho) +
                            String.fromCharCode(0x1161 + jung) +
                            (jong > 0 ? String.fromCharCode(0x11A7 + jong) : '');
                    }
                    return char;
                }).join('');
            };

            const decomposedText = decomposeHangul(normalizedText);
            const decomposedQuery = decomposeHangul(normalizedQuery);

            return decomposedText.includes(decomposedQuery);
        }

        return false;
    };

    const filteredDocuments = documents.filter(doc => {
        const matchesSearch = searchInText(doc.original_name, searchQuery);
        const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
        const matchesType = typeFilters.length === 0 || typeFilters.includes(getDocumentType(doc.mime_type, doc.filename));
        return matchesSearch && matchesStatus && matchesType;
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

    const getTypeCounts = () => {
        const counts: Record<string, number> = {};
        documents.forEach(doc => {
            const type = getDocumentType(doc.mime_type, doc.filename);
            counts[type] = (counts[type] || 0) + 1;
        });
        return counts;
    };

    const statusCounts = getStatusCounts();
    const typeCounts = getTypeCounts();

    // 타입 필터 토글 함수
    const toggleTypeFilter = (type: string) => {
        setTypeFilters(prev =>
            prev.includes(type)
                ? prev.filter(t => t !== type)
                : [...prev, type]
        );
    };

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

                    {/* 타입 필터 */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-600">문서 타입</span>
                            {typeFilters.length > 0 && (
                                <button
                                    onClick={() => setTypeFilters([])}
                                    className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                                >
                                    <X size={10} />
                                    모두 해제
                                </button>
                            )}
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {Object.entries(typeCounts)
                                .filter(([type, count]) => count > 0)
                                .sort(([a], [b]) => a.localeCompare(b))
                                .map(([type, count]) => {
                                    const typeInfo = getTypeInfo(type);
                                    const isSelected = typeFilters.includes(type);
                                    return (
                                        <button
                                            key={type}
                                            onClick={() => toggleTypeFilter(type)}
                                            className={`
                                                inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border transition-colors
                                                ${isSelected
                                                    ? `${typeInfo.color} border-current`
                                                    : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                                                }
                                            `}
                                        >
                                            {typeInfo.icon}
                                            {typeInfo.label}
                                            <span className="text-xs opacity-75">({count})</span>
                                        </button>
                                    );
                                })}
                        </div>
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
                    ) : hasError ? (
                        <div className="text-center text-gray-500 py-8">
                            <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
                            <div className="text-sm text-red-600 font-medium">문서를 불러오는데 실패했습니다</div>
                            <div className="text-xs text-gray-500 mt-1 mb-4">
                                서버 연결을 확인하고 다시 시도해주세요
                            </div>
                            {onRefresh && (
                                <button
                                    onClick={onRefresh}
                                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm"
                                >
                                    <RefreshCw size={14} className="inline mr-1" />
                                    다시 시도
                                </button>
                            )}
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

                                            {document.status === 'failed' && document.retryable && (
                                                <button
                                                    onClick={() => onRetry(document.id)}
                                                    className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded"
                                                    title="재시도"
                                                >
                                                    <RefreshCw size={12} />
                                                </button>
                                            )}

                                            {document.status === 'failed' && !document.retryable && (
                                                <span
                                                    className="p-1 text-gray-300"
                                                    title="재처리 불가능 (업로드 실패)"
                                                >
                                                    <RefreshCw size={12} />
                                                </span>
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
