'use client';

import { File, FileSpreadsheet, FileText, Image, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface DocumentPreviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    documentId: string;
    filename: string;
}

interface FileUrlResponse {
    download_url: string;
    content_type: string;
    filename: string;
}

interface ExcelSheet {
    sheet_name: string;
    headers: string[];
    rows: Array<Record<string, string>>;
    total_rows: number;
    total_columns: number;
}

interface ExcelPreviewData {
    document_id: number;
    filename: string;
    content_type: string;
    sheets: ExcelSheet[];
}

const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
    isOpen,
    onClose,
    documentId,
    filename
}) => {
    const [fileUrl, setFileUrl] = useState<string>('');
    const [previewText, setPreviewText] = useState<string>('');
    const [excelData, setExcelData] = useState<ExcelPreviewData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        if (isOpen && documentId) {
            fetchFileUrl();
        }
    }, [isOpen, documentId]);

    const fetchFileUrl = async () => {
        setLoading(true);
        setError('');
        try {
            const ext = filename.toLowerCase().split('.').pop();
            console.log('파일 확장자:', ext, '문서 ID:', documentId);

            // 엑셀/CSV 파일인 경우 표 형태 미리보기
            if (ext === 'xlsx' || ext === 'csv') {
                const url = `/api/v1/documents/${documentId}/excel-preview`;
                console.log('엑셀 미리보기 요청 URL:', url);

                // 캐시 방지 및 타임아웃 설정
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 8000);
                const resp = await fetch(`${url}?t=${Date.now()}`, {
                    cache: 'no-store',
                    keepalive: false,
                    signal: controller.signal,
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                clearTimeout(timeoutId);
                console.log('응답 상태:', resp.status, resp.statusText);

                if (!resp.ok) {
                    const errorText = await resp.text();
                    console.error('API 응답 에러:', errorText);
                    throw new Error(`미리보기 실패: ${resp.status} - ${errorText}`);
                }

                const data = await resp.json();
                console.log('엑셀 데이터 수신:', data);
                setExcelData(data);
                setPreviewText('');
                setFileUrl('');
            } else {
                // 이미지 파일인 경우 원본 이미지 표시
                if (ext === 'jpg' || ext === 'jpeg' || ext === 'png') {
                    const url = `/api/v1/documents/${documentId}/download`;
                    console.log('이미지 다운로드 URL:', url);

                    setFileUrl(url);
                    setPreviewText('');
                    setExcelData(null);
                } else {
                    // 다른 파일은 기존 방식으로 텍스트 미리보기
                    const url = `/api/v1/documents/${documentId}/chunks?chunk_index=0`;
                    console.log('텍스트 미리보기 요청 URL:', url);

                    // 캐시 방지 및 타임아웃 설정
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 8000);
                    const resp = await fetch(`${url}&t=${Date.now()}`, {
                        cache: 'no-store',
                        keepalive: false,
                        signal: controller.signal,
                        headers: {
                            'Accept': 'application/json'
                        }
                    });
                    clearTimeout(timeoutId);
                    console.log('응답 상태:', resp.status, resp.statusText);

                    if (!resp.ok) {
                        const errorText = await resp.text();
                        console.error('API 응답 에러:', errorText);
                        throw new Error(`미리보기 실패: ${resp.status} - ${errorText}`);
                    }

                    const data = await resp.json();
                    console.log('텍스트 데이터 수신:', data);
                    const first = data?.chunks?.[0]?.content || '';
                    setPreviewText(first);
                    setExcelData(null);
                    setFileUrl('');
                }
            }
        } catch (err) {
            console.error('파일 URL 조회 오류:', err);
            setError(`미리보기를 불러올 수 없습니다: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
        } finally {
            setLoading(false);
        }
    };

    const getFileIcon = () => {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'pdf':
                return <FileText className="w-8 h-8 text-red-500" />;
            case 'png':
            case 'jpg':
            case 'jpeg':
                return <Image className="w-8 h-8 text-green-500" />;
            case 'xlsx':
            case 'csv':
                return <FileSpreadsheet className="w-8 h-8 text-green-600" />;
            case 'docx':
                return <FileText className="w-8 h-8 text-blue-500" />;
            default:
                return <File className="w-8 h-8 text-gray-500" />;
        }
    };

    const renderExcelPreview = () => {
        if (!excelData || !excelData.sheets.length) {
            return (
                <div className="flex items-center justify-center h-96 text-gray-500">
                    <p>표시할 데이터가 없습니다.</p>
                </div>
            );
        }

        return (
            <div className="space-y-6">
                {excelData.sheets.map((sheet, sheetIndex) => (
                    <div key={sheetIndex} className="border rounded-lg overflow-hidden">
                        <div className="bg-gray-100 px-4 py-2 border-b">
                            <h4 className="font-semibold text-gray-800">
                                {sheet.sheet_name} ({sheet.total_rows}행 × {sheet.total_columns}열)
                            </h4>
                        </div>
                        <div className="overflow-auto max-h-96">
                            <table className="w-full border-collapse">
                                <thead className="bg-gray-50">
                                    <tr>
                                        {sheet.headers.map((header, index) => (
                                            <th
                                                key={index}
                                                className="border border-gray-300 px-3 py-2 text-left text-sm font-medium text-gray-700 bg-gray-100"
                                            >
                                                {header}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {sheet.rows.slice(0, 100).map((row, rowIndex) => (
                                        <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                            {sheet.headers.map((header, colIndex) => (
                                                <td
                                                    key={colIndex}
                                                    className="border border-gray-300 px-3 py-2 text-sm text-gray-800"
                                                >
                                                    {row[header] || ''}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {sheet.rows.length > 100 && (
                                <div className="text-center py-2 text-gray-500 text-sm">
                                    ... 총 {sheet.rows.length}행 중 100행만 표시
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    const renderPreview = () => {
        if (loading) {
            return (
                <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                    <div className="text-red-500 mb-2">⚠️</div>
                    <p>{error}</p>
                </div>
            );
        }

        // 엑셀/CSV 파일인 경우 표 형태 미리보기
        if (excelData) {
            return renderExcelPreview();
        }

        // 이미지 파일인 경우 원본 이미지 표시
        const ext = filename.toLowerCase().split('.').pop();
        if ((ext === 'jpg' || ext === 'jpeg' || ext === 'png') && fileUrl) {
            return (
                <div className="h-96 overflow-auto flex items-center justify-center bg-gray-50 rounded border">
                    <img
                        src={fileUrl}
                        alt={filename}
                        className="max-w-full max-h-full object-contain"
                        onError={(e) => {
                            console.error('이미지 로드 실패:', e);
                            setError('이미지를 불러올 수 없습니다.');
                        }}
                    />
                </div>
            );
        }

        // 텍스트 미리보기(첫 청크)
        return (
            <div className="h-96 overflow-auto rounded border bg-gray-50 p-3 whitespace-pre-wrap text-sm text-gray-800">
                {previewText || '미리볼 내용이 없습니다.'}
            </div>
        );
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <div className="flex items-center space-x-3">
                        {getFileIcon()}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">{filename}</h3>
                            <p className="text-sm text-gray-500">문서 미리보기</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-4">
                    {renderPreview()}
                </div>

                {/* Footer */}
                <div className="flex justify-end space-x-2 p-4 border-t bg-gray-50">
                    <button
                        onClick={() => window.location.href = `/api/v1/documents/${documentId}/download`}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                        다운로드
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DocumentPreviewModal;
