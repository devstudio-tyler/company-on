'use client';

import { Upload } from 'lucide-react';
import { memo, useCallback, useEffect, useState } from 'react';

interface GlobalDragDropProps {
    onFileDrop: (files: File[]) => void;
    children: React.ReactNode;
}

const GlobalDragDrop = memo(function GlobalDragDrop({
    onFileDrop,
    children
}: GlobalDragDropProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [dragCounter, setDragCounter] = useState(0);

    const resetDragState = useCallback(() => {
        setIsDragOver(false);
        setDragCounter(0);
    }, []);

    const handleDragEnter = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragCounter(prev => prev + 1);
        if (e.dataTransfer?.items && e.dataTransfer.items.length > 0) {
            setIsDragOver(true);
        }
    }, []);

    const handleDragLeave = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();

        // body나 html 요소에서 dragleave가 발생하면 브라우저 밖으로 나간 것으로 간주
        const target = e.target as Element;
        if (target === document.body || target === document.documentElement) {
            resetDragState();
            return;
        }

        setDragCounter(prev => {
            const newCounter = prev - 1;
            if (newCounter <= 0) {
                setIsDragOver(false);
                return 0;
            }
            return newCounter;
        });
    }, [resetDragState]);

    const handleDragOver = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        // 파일이 포함된 드래그인지 확인
        if (e.dataTransfer?.types?.includes('Files')) {
            setIsDragOver(true);
        }
    }, []);

    const handleDrop = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        resetDragState();

        if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
            const files = Array.from(e.dataTransfer.files);

            // 파일 타입 검증
            const allowedTypes = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                'image/png',
                'image/jpeg'
            ];

            const allowedExtensions = ['.pdf', '.docx', '.xlsx', '.csv', '.png', '.jpg', '.jpeg'];

            const validFiles: File[] = [];
            const invalidFiles: string[] = [];

            files.forEach(file => {
                const isValidType = allowedTypes.includes(file.type.toLowerCase());
                const isValidExtension = allowedExtensions.some(ext =>
                    file.name.toLowerCase().endsWith(ext)
                );

                if (isValidType || isValidExtension) {
                    validFiles.push(file);
                } else {
                    invalidFiles.push(file.name);
                }
            });

            if (invalidFiles.length > 0) {
                alert(`지원되지 않는 파일 형식입니다:\n${invalidFiles.join('\n')}\n\n지원 형식: PDF, DOCX, XLSX, CSV, PNG, JPG`);
            }

            if (validFiles.length > 0) {
                onFileDrop(validFiles);
            }
        }
    }, [onFileDrop, resetDragState]);

    useEffect(() => {
        const handleDragEnterGlobal = (e: DragEvent) => handleDragEnter(e);
        const handleDragLeaveGlobal = (e: DragEvent) => handleDragLeave(e);
        const handleDragOverGlobal = (e: DragEvent) => handleDragOver(e);
        const handleDropGlobal = (e: DragEvent) => handleDrop(e);

        // 브라우저 밖으로 드래그가 나갔을 때 감지
        const handleMouseEnter = () => {
            // 마우스가 브라우저 영역으로 다시 들어왔을 때는 아무것도 하지 않음
        };

        const handleMouseLeave = () => {
            // 마우스가 브라우저 밖으로 나갔을 때 드래그 상태 리셋
            if (isDragOver) {
                resetDragState();
            }
        };

        // 윈도우 포커스 변경 시에도 드래그 상태 리셋
        const handleWindowBlur = () => {
            if (isDragOver) {
                resetDragState();
            }
        };

        document.addEventListener('dragenter', handleDragEnterGlobal);
        document.addEventListener('dragleave', handleDragLeaveGlobal);
        document.addEventListener('dragover', handleDragOverGlobal);
        document.addEventListener('drop', handleDropGlobal);
        document.addEventListener('mouseenter', handleMouseEnter);
        document.addEventListener('mouseleave', handleMouseLeave);
        window.addEventListener('blur', handleWindowBlur);

        return () => {
            document.removeEventListener('dragenter', handleDragEnterGlobal);
            document.removeEventListener('dragleave', handleDragLeaveGlobal);
            document.removeEventListener('dragover', handleDragOverGlobal);
            document.removeEventListener('drop', handleDropGlobal);
            document.removeEventListener('mouseenter', handleMouseEnter);
            document.removeEventListener('mouseleave', handleMouseLeave);
            window.removeEventListener('blur', handleWindowBlur);
        };
    }, [handleDragEnter, handleDragLeave, handleDragOver, handleDrop, isDragOver, resetDragState]);

    return (
        <div className="relative h-full">
            {children}

            {/* 드래그 오버레이 */}
            {isDragOver && (
                <div
                    className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center"
                    onClick={resetDragState}
                >
                    <div className="bg-white rounded-lg p-8 text-center shadow-xl" onClick={(e) => e.stopPropagation()}>
                        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                            <Upload size={32} className="text-blue-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            파일을 여기에 놓으세요
                        </h3>
                        <p className="text-gray-600">
                            PDF, DOCX, TXT 파일을 업로드할 수 있습니다
                        </p>
                        <p className="text-sm text-gray-400 mt-2">
                            클릭하면 닫힙니다
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
});

export default GlobalDragDrop;

