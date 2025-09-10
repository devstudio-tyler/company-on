'use client';

import { X } from 'lucide-react';
import { useState } from 'react';

interface NewSessionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreateSession: (title?: string) => void;
}

export default function NewSessionModal({ isOpen, onClose, onCreateSession }: NewSessionModalProps) {
    const [title, setTitle] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreateSession(title.trim() || undefined);
        setTitle('');
        onClose();
    };

    const handleClose = () => {
        setTitle('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">새 세션 생성</h2>
                    <button
                        onClick={handleClose}
                        className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6">
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="session-title" className="block text-sm font-medium text-gray-700 mb-2">
                                세션 제목 (선택사항)
                            </label>
                            <input
                                id="session-title"
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="제목을 입력하지 않으면 자동으로 생성됩니다"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                제목을 입력하지 않으면 "{new Date().toLocaleDateString('ko-KR')}의 새 채팅"으로 설정됩니다.
                            </p>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={handleClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            세션 생성
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
