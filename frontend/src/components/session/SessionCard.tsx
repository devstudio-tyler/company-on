'use client';

import { ChatSession } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import { Calendar, Edit, MessageSquare, Pin, Tag, Trash2 } from 'lucide-react';
import { memo } from 'react';

interface SessionCardProps {
    session: ChatSession;
    isSelected: boolean;
    onSelect: (sessionId: string) => void;
    onPin: (sessionId: string) => void;
    onEdit: (session: ChatSession) => void;
    onDelete: (sessionId: string) => void;
}

const SessionCard = memo(function SessionCard({
    session,
    isSelected,
    onSelect,
    onPin,
    onEdit,
    onDelete
}: SessionCardProps) {
    const handleClick = () => {
        onSelect(session.id);
    };

    const handlePinClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onPin(session.id);
    };

    const handleEditClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onEdit(session);
    };

    const handleDeleteClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(session.id);
    };

    return (
        <div
            className={`
                group relative p-3 rounded-lg cursor-pointer transition-all duration-200
                ${isSelected
                    ? 'bg-blue-50 border-2 border-blue-200 shadow-sm'
                    : 'bg-white border border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }
            `}
            onClick={handleClick}
        >
            {/* 액션 버튼 (수정/삭제는 hover시에만, 핀은 고정 시 항상 표시) */}
            <div className="absolute top-2 right-2 flex items-center gap-1">
                <button
                    onClick={handleEditClick}
                    className="p-1 rounded text-gray-400 hover:text-blue-500 hover:bg-blue-50 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="수정"
                >
                    <Edit size={12} />
                </button>
                <button
                    onClick={handleDeleteClick}
                    className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="삭제"
                >
                    <Trash2 size={12} />
                </button>
                <button
                    onClick={handlePinClick}
                    className={`p-1 rounded transition-colors ${session.is_pinned ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500 opacity-0 group-hover:opacity-100'}`}
                    title={session.is_pinned ? '고정 해제' : '상단 고정'}
                >
                    <Pin size={14} className={session.is_pinned ? 'fill-current' : ''} />
                </button>
            </div>

            {/* 세션 제목 */}
            <h3 className="font-medium text-gray-900 text-sm mb-1 pr-6 line-clamp-2">
                {session.title}
            </h3>

            {/* 세션 설명 */}
            <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                {session.description}
            </p>

            {/* 태그 */}
            {session.tags && session.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                    {session.tags.slice(0, 2).map((tag, index) => (
                        <span
                            key={index}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
                        >
                            <Tag size={10} className="mr-1" />
                            {tag}
                        </span>
                    ))}
                    {session.tags.length > 2 && (
                        <span className="text-xs text-gray-400">
                            +{session.tags.length - 2}
                        </span>
                    )}
                </div>
            )}

            {/* 메타 정보 */}
            <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-1">
                    <MessageSquare size={12} />
                    <span>{session.message_count || 0}</span>
                </div>
                <div className="flex items-center gap-1">
                    <Calendar size={12} />
                    <span>
                        {formatDistanceToNow(new Date(session.updated_at), {
                            addSuffix: true,
                            locale: ko
                        })}
                    </span>
                </div>
            </div>

            {/* 액션 버튼 Row는 상단으로 이동 */}
        </div>
    );
});

export default SessionCard;
