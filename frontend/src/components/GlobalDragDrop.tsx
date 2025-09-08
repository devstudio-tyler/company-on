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
        setDragCounter(prev => prev - 1);
        if (dragCounter <= 1) {
            setIsDragOver(false);
        }
    }, [dragCounter]);

    const handleDragOver = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
        setDragCounter(0);

        if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
            const files = Array.from(e.dataTransfer.files);
            onFileDrop(files);
        }
    }, [onFileDrop]);

    useEffect(() => {
        const handleDragEnterGlobal = (e: DragEvent) => handleDragEnter(e);
        const handleDragLeaveGlobal = (e: DragEvent) => handleDragLeave(e);
        const handleDragOverGlobal = (e: DragEvent) => handleDragOver(e);
        const handleDropGlobal = (e: DragEvent) => handleDrop(e);

        document.addEventListener('dragenter', handleDragEnterGlobal);
        document.addEventListener('dragleave', handleDragLeaveGlobal);
        document.addEventListener('dragover', handleDragOverGlobal);
        document.addEventListener('drop', handleDropGlobal);

        return () => {
            document.removeEventListener('dragenter', handleDragEnterGlobal);
            document.removeEventListener('dragleave', handleDragLeaveGlobal);
            document.removeEventListener('dragover', handleDragOverGlobal);
            document.removeEventListener('drop', handleDropGlobal);
        };
    }, [handleDragEnter, handleDragLeave, handleDragOver, handleDrop]);

    return (
        <div className="relative h-full">
            {children}

            {/* 드래그 오버레이 */}
            {isDragOver && (
                <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-8 text-center shadow-xl">
                        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                            <Upload size={32} className="text-blue-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            파일을 여기에 놓으세요
                        </h3>
                        <p className="text-gray-600">
                            PDF, DOCX, TXT 파일을 업로드할 수 있습니다
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
});

export default GlobalDragDrop;

