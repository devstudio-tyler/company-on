'use client';

import { Download, ExternalLink, X } from 'lucide-react';
import { memo, useEffect, useState } from 'react';

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

interface DocumentPreviewProps {
    document: Document | null;
    isOpen: boolean;
    onClose: () => void;
    onDownload: (documentId: string) => void;
}

const DocumentPreview = memo(function DocumentPreview({
    document,
    isOpen,
    onClose,
    onDownload
}: DocumentPreviewProps) {
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (document && isOpen) {
            loadPreview();
        } else {
            setPreviewUrl(null);
            setError(null);
        }
    }, [document, isOpen]);

    const loadPreview = async () => {
        if (!document) return;

        setIsLoading(true);
        setError(null);

        try {
            // TODO: 실제 API에서 미리보기 URL 가져오기
            // const response = await api.getDocumentPreview(document.id);
            // setPreviewUrl(response.preview_url);

            // 임시로 파일 타입에 따라 다른 미리보기 표시
            if (document.mime_type.includes('pdf')) {
                // PDF 미리보기 (PDF.js 사용)
                setPreviewUrl(`/api/documents/${document.id}/preview`);
            } else if (document.mime_type.includes('text')) {
                // 텍스트 파일 미리보기
                setPreviewUrl(`/api/documents/${document.id}/content`);
            } else {
                setError('미리보기를 지원하지 않는 파일 형식입니다.');
            }
        } catch (err) {
            setError('미리보기를 불러올 수 없습니다.');
            console.error('Preview load error:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDownload = () => {
        if (document) {
            onDownload(document.id);
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    if (!isOpen || !document) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 mx-4 flex flex-col">
                {/* 헤더 */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <div className="flex items-center space-x-3">
                        <div className="text-2xl">
                            {document.mime_type.includes('pdf') ? '📄' :
                                document.mime_type.includes('word') ? '📝' : '📄'}
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">
                                {document.original_name}
                            </h2>
                            <p className="text-sm text-gray-500">
                                {formatFileSize(document.file_size)} •
                                {document.mime_type}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <button
                            onClick={handleDownload}
                            className="inline-flex items-center px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                        >
                            <Download size={16} className="mr-2" />
                            다운로드
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* 미리보기 영역 */}
                <div className="flex-1 p-4 overflow-hidden">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                                <p className="text-gray-500">미리보기를 불러오는 중...</p>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center">
                                <div className="text-red-500 mb-4">
                                    <ExternalLink size={48} className="mx-auto" />
                                </div>
                                <p className="text-gray-700 mb-2">{error}</p>
                                <button
                                    onClick={handleDownload}
                                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                >
                                    <Download size={16} className="mr-2" />
                                    파일 다운로드
                                </button>
                            </div>
                        </div>
                    ) : previewUrl ? (
                        <div className="h-full">
                            {document.mime_type.includes('pdf') ? (
                                <iframe
                                    src={previewUrl}
                                    className="w-full h-full border-0 rounded"
                                    title={`${document.original_name} 미리보기`}
                                />
                            ) : document.mime_type.includes('text') ? (
                                <iframe
                                    src={previewUrl}
                                    className="w-full h-full border-0 rounded"
                                    title={`${document.original_name} 미리보기`}
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full">
                                    <div className="text-center">
                                        <div className="text-6xl mb-4">
                                            {document.mime_type.includes('pdf') ? '📄' : '📝'}
                                        </div>
                                        <p className="text-gray-700 mb-4">
                                            {document.original_name}
                                        </p>
                                        <button
                                            onClick={handleDownload}
                                            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                        >
                                            <Download size={16} className="mr-2" />
                                            파일 다운로드
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center">
                                <div className="text-6xl mb-4">
                                    {document.mime_type.includes('pdf') ? '📄' : '📝'}
                                </div>
                                <p className="text-gray-700 mb-4">
                                    {document.original_name}
                                </p>
                                <button
                                    onClick={handleDownload}
                                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                >
                                    <Download size={16} className="mr-2" />
                                    파일 다운로드
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* 하단 정보 */}
                <div className="p-4 border-t border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                            <span>업로드: {new Date(document.created_at).toLocaleString('ko-KR')}</span>
                            <span>수정: {new Date(document.updated_at).toLocaleString('ko-KR')}</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            {document.chunk_count && (
                                <span>청크: {document.chunk_count}개</span>
                            )}
                            {document.embedding_count && (
                                <span>임베딩: {document.embedding_count}개</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
});

export default DocumentPreview;

