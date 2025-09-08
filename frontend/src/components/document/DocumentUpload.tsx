'use client';

import { AlertCircle, File, Upload, X } from 'lucide-react';
import { memo, useCallback, useState } from 'react';

interface UploadFile {
    id: string;
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

interface DocumentUploadProps {
    onUpload: (files: File[]) => void;
    onRemove: (fileId: string) => void;
    maxFiles?: number;
    acceptedTypes?: string[];
    maxSize?: number; // MB
}

const DocumentUpload = memo(function DocumentUpload({
    onUpload,
    onRemove,
    maxFiles = 10,
    acceptedTypes = ['.pdf', '.docx', '.txt'],
    maxSize = 50
}: DocumentUploadProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);

    const validateFile = (file: File): string | null => {
        // 파일 크기 검증
        if (file.size > maxSize * 1024 * 1024) {
            return `파일 크기가 ${maxSize}MB를 초과합니다.`;
        }

        // 파일 타입 검증
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!acceptedTypes.includes(fileExtension)) {
            return `지원하지 않는 파일 형식입니다. (${acceptedTypes.join(', ')} 허용)`;
        }

        return null;
    };

    const handleFiles = useCallback((files: FileList | File[]) => {
        const fileArray = Array.from(files);
        const validFiles: File[] = [];
        const errors: string[] = [];

        fileArray.forEach(file => {
            const error = validateFile(file);
            if (error) {
                errors.push(`${file.name}: ${error}`);
            } else {
                validFiles.push(file);
            }
        });

        if (errors.length > 0) {
            alert(errors.join('\n'));
        }

        if (validFiles.length > 0) {
            const newUploadFiles: UploadFile[] = validFiles.map(file => ({
                id: Math.random().toString(36).substr(2, 9),
                file,
                status: 'pending',
                progress: 0
            }));

            setUploadFiles(prev => [...prev, ...newUploadFiles].slice(0, maxFiles));
            onUpload(validFiles);
        }
    }, [maxFiles, maxSize, acceptedTypes, onUpload]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        handleFiles(e.dataTransfer.files);
    }, [handleFiles]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            handleFiles(e.target.files);
        }
    }, [handleFiles]);

    const handleRemoveFile = useCallback((fileId: string) => {
        setUploadFiles(prev => prev.filter(f => f.id !== fileId));
        onRemove(fileId);
    }, [onRemove]);

    const getFileIcon = (fileName: string) => {
        const extension = fileName.split('.').pop()?.toLowerCase();
        switch (extension) {
            case 'pdf':
                return '📄';
            case 'docx':
            case 'doc':
                return '📝';
            case 'txt':
                return '📄';
            default:
                return '📄';
        }
    };

    const getStatusColor = (status: UploadFile['status']) => {
        switch (status) {
            case 'pending':
                return 'text-gray-500';
            case 'uploading':
                return 'text-blue-500';
            case 'success':
                return 'text-green-500';
            case 'error':
                return 'text-red-500';
            default:
                return 'text-gray-500';
        }
    };

    return (
        <div className="w-full">
            {/* 드래그 앤 드롭 영역 */}
            <div
                className={`
                    relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
                    ${isDragOver
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    multiple
                    accept={acceptedTypes.join(',')}
                    onChange={handleFileInput}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />

                <div className="space-y-4">
                    <div className="mx-auto w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                        <Upload size={24} className="text-gray-400" />
                    </div>

                    <div>
                        <p className="text-lg font-medium text-gray-900">
                            파일을 여기에 드래그하거나 클릭하여 업로드
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                            {acceptedTypes.join(', ')} 파일만 업로드 가능 (최대 {maxSize}MB)
                        </p>
                    </div>

                    <button
                        type="button"
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <File size={16} className="mr-2" />
                        파일 선택
                    </button>
                </div>
            </div>

            {/* 업로드 파일 목록 */}
            {uploadFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                    <h3 className="text-sm font-medium text-gray-700">업로드할 파일</h3>
                    <div className="space-y-2">
                        {uploadFiles.map((uploadFile) => (
                            <div
                                key={uploadFile.id}
                                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                            >
                                <div className="flex items-center space-x-3 flex-1 min-w-0">
                                    <span className="text-lg">
                                        {getFileIcon(uploadFile.file.name)}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate">
                                            {uploadFile.file.name}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            {(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                    {/* 상태 표시 */}
                                    <div className={`text-xs ${getStatusColor(uploadFile.status)}`}>
                                        {uploadFile.status === 'pending' && '대기중'}
                                        {uploadFile.status === 'uploading' && '업로드중'}
                                        {uploadFile.status === 'success' && '완료'}
                                        {uploadFile.status === 'error' && '오류'}
                                    </div>

                                    {/* 진행률 표시 */}
                                    {uploadFile.status === 'uploading' && (
                                        <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500 transition-all duration-300"
                                                style={{ width: `${uploadFile.progress}%` }}
                                            />
                                        </div>
                                    )}

                                    {/* 에러 메시지 */}
                                    {uploadFile.status === 'error' && uploadFile.error && (
                                        <div className="flex items-center text-red-500">
                                            <AlertCircle size={14} className="mr-1" />
                                            <span className="text-xs">{uploadFile.error}</span>
                                        </div>
                                    )}

                                    {/* 제거 버튼 */}
                                    <button
                                        onClick={() => handleRemoveFile(uploadFile.id)}
                                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
});

export default DocumentUpload;

