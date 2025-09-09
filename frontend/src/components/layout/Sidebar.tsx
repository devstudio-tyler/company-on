'use client';

import { updateSession, updateSessionPin } from '@/lib/api/sessions';
import { getClientId } from '@/lib/utils';
import { ChatSession } from '@/types';
import {
    AlertCircle,
    FileText,
    RefreshCw
} from 'lucide-react';
import { useEffect, useState } from 'react';
import SessionCard from '../session/SessionCard';
import SessionModal from '../session/SessionModal';
import SessionSearch from '../session/SessionSearch';

interface SidebarProps {
    sessions: ChatSession[];
    currentSessionId?: string;
    onSessionSelect: (sessionId: string) => void;
    onNewSession: () => void;
    onSearch: (query: string) => void;
    onSessionUpdate: (session: ChatSession) => void;
    onSessionDelete: (sessionId: string) => void;
    onModeChange?: (mode: 'session' | 'document') => void;
    currentMode?: 'session' | 'document';
    className?: string;
    isLoading?: boolean;
    isInitialLoad?: boolean;
    hasError?: boolean;
    onRefresh?: () => void;
}

function SessionSidebar({
    sessions,
    currentSessionId,
    onSessionSelect,
    onNewSession,
    onSearch,
    onSessionUpdate,
    onSessionDelete,
    onModeChange,
    currentMode = 'session',
    className = '',
    isLoading = false,
    isInitialLoad = false,
    hasError = false,
    onRefresh
}: SidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingSession, setEditingSession] = useState<ChatSession | null>(null);
    const [filteredSessions, setFilteredSessions] = useState<ChatSession[]>(sessions);
    const [isModalLoading, setIsModalLoading] = useState(false);

    // sessions가 변경될 때 filteredSessions 동기화
    useEffect(() => {
        setFilteredSessions(sessions);
    }, [sessions]);

    const handleSearch = (query: string) => {
        onSearch(query);
        const filtered = sessions.filter(session =>
            session.title.toLowerCase().includes(query.toLowerCase()) ||
            session.description?.toLowerCase().includes(query.toLowerCase())
        );
        setFilteredSessions(filtered);
    };

    const handleFilterChange = (filters: any) => {
        let filtered = sessions;

        // 쿼리 필터
        if (filters.query) {
            filtered = filtered.filter(session =>
                session.title.toLowerCase().includes(filters.query.toLowerCase()) ||
                session.description?.toLowerCase().includes(filters.query.toLowerCase())
            );
        }

        // 태그 필터
        if (filters.tags && filters.tags.length > 0) {
            filtered = filtered.filter(session =>
                session.tags && session.tags.some(tag => filters.tags.includes(tag))
            );
        }

        // 핀 필터
        if (filters.isPinned !== null) {
            filtered = filtered.filter(session => session.is_pinned === filters.isPinned);
        }

        // 날짜 범위 필터
        if (filters.dateRange) {
            const startDate = new Date(filters.dateRange.start);
            const endDate = new Date(filters.dateRange.end);
            filtered = filtered.filter(session => {
                const sessionDate = new Date(session.updated_at);
                return sessionDate >= startDate && sessionDate <= endDate;
            });
        }

        setFilteredSessions(filtered);
    };

    const handleNewSession = () => {
        setEditingSession(null);
        setIsModalOpen(true);
    };

    const handleEditSession = (session: ChatSession) => {
        setEditingSession(session);
        setIsModalOpen(true);
    };

    const handleSessionSave = async (sessionData: Omit<ChatSession, 'id' | 'created_at' | 'updated_at' | 'message_count'>) => {
        if (editingSession) {
            // 로딩 상태 시작
            setIsModalLoading(true);

            // 기존 세션 수정 - 낙관적 업데이트
            const optimisticSession: ChatSession = {
                ...editingSession,
                ...sessionData,
                updated_at: new Date().toISOString()
            };

            // 즉시 UI 업데이트
            onSessionUpdate(optimisticSession);

            // 백그라운드에서 API 호출
            try {
                const clientId = getClientId();
                // 모든 필드를 한 번에 업데이트
                const updatedSession = await updateSession(
                    editingSession.id,
                    sessionData.title,
                    sessionData.description || '',
                    sessionData.tags || [],
                    sessionData.is_pinned,
                    clientId
                );
                // API 성공 시 서버 데이터로 업데이트
                onSessionUpdate(updatedSession);
            } catch (error) {
                console.error('세션 수정 실패:', error);
                // API 실패 시 원래 데이터로 롤백
                onSessionUpdate(editingSession);
                alert('세션 수정에 실패했습니다. 변경사항이 되돌려졌습니다.');
            } finally {
                // 로딩 완료 후 모달 닫기
                setIsModalLoading(false);
                setIsModalOpen(false);
            }
        } else {
            // 새 세션 생성은 부모 컴포넌트에서 처리
            const newSession: ChatSession = {
                id: Date.now().toString(),
                ...sessionData,
                client_id: 'default-client',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                message_count: 0
            };
            onSessionUpdate(newSession);
            setIsModalOpen(false);
        }
    };

    const handleSessionPin = async (sessionId: string) => {
        const session = sessions.find(s => s.id === sessionId);
        if (session) {
            // 낙관적 업데이트 - 즉시 UI 업데이트
            const optimisticSession: ChatSession = {
                ...session,
                is_pinned: !session.is_pinned,
                updated_at: new Date().toISOString()
            };
            onSessionUpdate(optimisticSession);

            // 백그라운드에서 API 호출
            try {
                const clientId = getClientId();
                const updatedSession = await updateSessionPin(sessionId, !session.is_pinned, clientId);
                // API 성공 시 서버 데이터로 업데이트
                onSessionUpdate(updatedSession);
            } catch (error) {
                console.error('세션 고정 상태 업데이트 실패:', error);
                // API 실패 시 원래 데이터로 롤백
                onSessionUpdate(session);
                alert('세션 고정 상태 업데이트에 실패했습니다. 변경사항이 되돌려졌습니다.');
            }
        }
    };

    return (
        <div className={`bg-white border-r border-gray-200 flex flex-col h-full transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-80'
            } ${className}`}>
            {/* 헤더 - 모드 선택 */}
            <div className="border-b border-gray-200 px-3 py-3">
                <div className="flex items-center justify-between">
                    {!isCollapsed && onModeChange ? (
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
                    ) : !isCollapsed ? (
                        <h1 className="text-xl font-bold text-gray-900">Company-on</h1>
                    ) : null}
                    {/* 세션 모드에서도 X 버튼 노출하지 않음 (헤더의 햄버거로 제어) */}
                </div>
            </div>

            {/* 검색 및 필터 */}
            {!isCollapsed && (
                <SessionSearch
                    onSearch={handleSearch}
                    onFilterChange={handleFilterChange}
                    placeholder="세션 검색..."
                />
            )}


            {/* 세션 리스트 */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-2">
                    {isLoading || isInitialLoad ? (
                        <div className="text-center text-gray-500 py-8">
                            <RefreshCw size={32} className="mx-auto mb-2 text-gray-400 animate-spin" />
                            <div className="text-sm">세션을 불러오는 중...</div>
                            <div className="text-xs text-gray-400 mt-1">
                                잠시만 기다려주세요
                            </div>
                        </div>
                    ) : hasError ? (
                        <div className="text-center text-gray-500 py-8">
                            <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
                            <div className="text-sm text-red-600 font-medium">세션을 불러오는데 실패했습니다</div>
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
                    ) : filteredSessions.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <div className="text-sm">세션이 없습니다</div>
                            <div className="text-xs text-gray-400 mt-1">
                                새 세션을 만들어보세요
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {filteredSessions
                                .sort((a, b) => {
                                    // 핀된 세션을 먼저, 그 다음 업데이트 시간 순
                                    if (a.is_pinned && !b.is_pinned) return -1;
                                    if (!a.is_pinned && b.is_pinned) return 1;
                                    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
                                })
                                .map((session, index) => (
                                    <SessionCard
                                        key={`${session.id}-${index}`}
                                        session={session}
                                        isSelected={currentSessionId === session.id}
                                        onSelect={onSessionSelect}
                                        onPin={handleSessionPin}
                                        onEdit={handleEditSession}
                                        onDelete={onSessionDelete}
                                    />
                                ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 하단 네비게이션 (세션 모드에서는 문서 관리 버튼 숨김) */}
            <div className="p-4 border-t border-gray-200">
                <div className="space-y-1">
                    {currentMode === 'document' && (
                        <a
                            href="/documents"
                            className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <FileText className="w-4 h-4" />
                            {!isCollapsed && <span>문서 관리</span>}
                        </a>
                    )}
                </div>
            </div>

            {/* 세션 모달 */}
            <SessionModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSessionSave}
                session={editingSession}
                mode={editingSession ? 'edit' : 'create'}
                isLoading={isModalLoading}
            />
        </div>
    );
}

export { SessionSidebar };
export default SessionSidebar;
