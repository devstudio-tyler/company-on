'use client';

import { Filter, Search, X } from 'lucide-react';
import { memo, useState } from 'react';

interface SessionSearchProps {
    onSearch: (query: string) => void;
    onFilterChange: (filters: SearchFilters) => void;
    placeholder?: string;
}

interface SearchFilters {
    query: string;
    tags: string[];
    isPinned: boolean | null;
    dateRange: {
        start: string;
        end: string;
    } | null;
}

const SessionSearch = memo(function SessionSearch({
    onSearch,
    onFilterChange,
    placeholder = "세션 검색..."
}: SessionSearchProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [filters, setFilters] = useState<SearchFilters>({
        query: '',
        tags: [],
        isPinned: null,
        dateRange: null
    });
    const [newTag, setNewTag] = useState('');

    const handleQueryChange = (query: string) => {
        const newFilters = { ...filters, query };
        setFilters(newFilters);
        onSearch(query);
        onFilterChange(newFilters);
    };

    const handleAddTag = () => {
        if (newTag.trim() && !filters.tags.includes(newTag.trim())) {
            const newTags = [...filters.tags, newTag.trim()];
            const newFilters = { ...filters, tags: newTags };
            setFilters(newFilters);
            onFilterChange(newFilters);
            setNewTag('');
        }
    };

    const handleRemoveTag = (tagToRemove: string) => {
        const newTags = filters.tags.filter(tag => tag !== tagToRemove);
        const newFilters = { ...filters, tags: newTags };
        setFilters(newFilters);
        onFilterChange(newFilters);
    };

    const handlePinFilterChange = (isPinned: boolean | null) => {
        const newFilters = { ...filters, isPinned };
        setFilters(newFilters);
        onFilterChange(newFilters);
    };

    const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
        const newDateRange = {
            ...filters.dateRange,
            [field]: value
        } as SearchFilters['dateRange'];

        const newFilters = { ...filters, dateRange: newDateRange };
        setFilters(newFilters);
        onFilterChange(newFilters);
    };

    const clearFilters = () => {
        const newFilters: SearchFilters = {
            query: '',
            tags: [],
            isPinned: null,
            dateRange: null
        };
        setFilters(newFilters);
        onSearch('');
        onFilterChange(newFilters);
    };

    const hasActiveFilters = filters.query || filters.tags.length > 0 || filters.isPinned !== null || filters.dateRange;

    return (
        <div className="p-3 border-b border-gray-200">
            {/* 검색 입력 */}
            <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                    type="text"
                    value={filters.query}
                    onChange={(e) => handleQueryChange(e.target.value)}
                    placeholder={placeholder}
                    className="w-full pl-9 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {filters.query && (
                    <button
                        onClick={() => handleQueryChange('')}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                        <X size={16} />
                    </button>
                )}
            </div>

            {/* 필터 토글 버튼 */}
            <div className="flex items-center justify-between mt-2">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
                >
                    <Filter size={14} />
                    필터
                    {hasActiveFilters && (
                        <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full">
                            {[filters.query, ...filters.tags, filters.isPinned !== null, filters.dateRange].filter(Boolean).length}
                        </span>
                    )}
                </button>

                {hasActiveFilters && (
                    <button
                        onClick={clearFilters}
                        className="text-sm text-gray-500 hover:text-gray-700"
                    >
                        필터 초기화
                    </button>
                )}
            </div>

            {/* 확장된 필터 옵션들 */}
            {isExpanded && (
                <div className="mt-3 space-y-3 p-3 bg-gray-50 rounded-md">
                    {/* 태그 필터 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            태그
                        </label>
                        <div className="flex gap-2 mb-2">
                            <input
                                type="text"
                                value={newTag}
                                onChange={(e) => setNewTag(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                placeholder="태그 추가"
                            />
                            <button
                                type="button"
                                onClick={handleAddTag}
                                className="px-2 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                            >
                                추가
                            </button>
                        </div>
                        {filters.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                                {filters.tags.map((tag, index) => (
                                    <span
                                        key={index}
                                        className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                                    >
                                        {tag}
                                        <button
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

                    {/* 핀 필터 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            고정 상태
                        </label>
                        <div className="flex gap-2">
                            <button
                                onClick={() => handlePinFilterChange(null)}
                                className={`px-3 py-1 text-sm rounded ${filters.isPinned === null
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                    }`}
                            >
                                전체
                            </button>
                            <button
                                onClick={() => handlePinFilterChange(true)}
                                className={`px-3 py-1 text-sm rounded ${filters.isPinned === true
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                    }`}
                            >
                                고정됨
                            </button>
                            <button
                                onClick={() => handlePinFilterChange(false)}
                                className={`px-3 py-1 text-sm rounded ${filters.isPinned === false
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                    }`}
                            >
                                일반
                            </button>
                        </div>
                    </div>

                    {/* 날짜 범위 필터 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            날짜 범위
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="date"
                                value={filters.dateRange?.start || ''}
                                onChange={(e) => handleDateRangeChange('start', e.target.value)}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <span className="text-gray-500">~</span>
                            <input
                                type="date"
                                value={filters.dateRange?.end || ''}
                                onChange={(e) => handleDateRangeChange('end', e.target.value)}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
});

export default SessionSearch;

