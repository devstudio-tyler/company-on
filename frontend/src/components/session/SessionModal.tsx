'use client';

import { ChatSession } from '@/types';
import { Plus, Tag, X } from 'lucide-react';
import { memo, useState } from 'react';

interface SessionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (session: Omit<ChatSession, 'id' | 'created_at' | 'updated_at' | 'message_count'>) => void;
    session?: ChatSession | null;
    mode: 'create' | 'edit';
}

const SessionModal = memo(function SessionModal({
    isOpen,
    onClose,
    onSave,
    session,
    mode
}: SessionModalProps) {
    const [formData, setFormData] = useState({
        title: session?.title || '',
        description: session?.description || '',
        tags: session?.tags || [],
        is_pinned: session?.is_pinned || false
    });
    const [newTag, setNewTag] = useState('');

    const handleInputChange = (field: string, value: string | boolean) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleAddTag = () => {
        if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
            setFormData(prev => ({
                ...prev,
                tags: [...prev.tags, newTag.trim()]
            }));
            setNewTag('');
        }
    };

    const handleRemoveTag = (tagToRemove: string) => {
        setFormData(prev => ({
            ...prev,
            tags: prev.tags.filter(tag => tag !== tagToRemove)
        }));
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddTag();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.title.trim()) {
            onSave(formData);
            onClose();
        }
    };

    const handleClose = () => {
        setFormData({
            title: '',
            description: '',
            tags: [],
            is_pinned: false
        });
        setNewTag('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                {/* 헤더 */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">
                        {mode === 'create' ? '새 채팅 세션' : '세션 수정'}
                    </h2>
                    <button
                        onClick={handleClose}
                        className="p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* 폼 */}
                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    {/* 제목 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            제목 *
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={(e) => handleInputChange('title', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="세션 제목을 입력하세요"
                            required
                        />
                    </div>

                    {/* 설명 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            설명
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => handleInputChange('description', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="세션에 대한 간단한 설명을 입력하세요"
                            rows={3}
                        />
                    </div>

                    {/* 태그 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            태그
                        </label>
                        <div className="flex gap-2 mb-2">
                            <input
                                type="text"
                                value={newTag}
                                onChange={(e) => setNewTag(e.target.value)}
                                onKeyPress={handleKeyPress}
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="태그를 입력하고 Enter를 누르세요"
                            />
                            <button
                                type="button"
                                onClick={handleAddTag}
                                className="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <Plus size={16} />
                            </button>
                        </div>
                        {formData.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                                {formData.tags.map((tag, index) => (
                                    <span
                                        key={index}
                                        className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                                    >
                                        <Tag size={10} className="mr-1" />
                                        {tag}
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveTag(tag)}
                                            className="ml-1 text-blue-600 hover:text-blue-800"
                                        >
                                            ×
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* 핀 설정 */}
                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="is_pinned"
                            checked={formData.is_pinned}
                            onChange={(e) => handleInputChange('is_pinned', e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="is_pinned" className="ml-2 text-sm text-gray-700">
                            상단에 고정
                        </label>
                    </div>

                    {/* 버튼들 */}
                    <div className="flex gap-2 pt-4">
                        <button
                            type="button"
                            onClick={handleClose}
                            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {mode === 'create' ? '생성' : '수정'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
});

export default SessionModal;

