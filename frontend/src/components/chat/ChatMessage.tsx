'use client';

import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  Bot,
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  FileText,
  Image,
  Table,
  ThumbsDown,
  ThumbsUp,
  User
} from 'lucide-react';
import { useState } from 'react';
import DocumentPreviewModal from '../DocumentPreviewModal';

export interface Source {
  index: string;
  title: string;
  filename: string;
  score: string;
  download_url?: string;
  preview_url?: string;
  content_preview: string;
  document_id: string;
  chunk_index: string;
  chunk_type?: string;
  metadata?: Record<string, any>;
  is_image?: boolean;
  image_url?: string;
}

interface DocumentSourceCardProps {
  documentId: string;
  title: string;
  filename: string;
  chunks: Source[];
}

function DocumentSourceCard({ documentId, title, filename, chunks }: DocumentSourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  // 파일 타입에 따른 아이콘 결정
  const getFileIcon = () => {
    const ext = filename.toLowerCase().split('.').pop();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) {
      return <Image size={16} className="text-blue-500" />;
    } else if (['xlsx', 'xls', 'csv'].includes(ext || '')) {
      return <Table size={16} className="text-green-500" />;
    }
    return <FileText size={16} className="text-gray-500" />;
  };

  // 파일 타입에 따른 미리보기 렌더링
  const renderChunkPreview = (chunk: Source) => {
    const ext = filename.toLowerCase().split('.').pop();

    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '') || chunk.is_image) {
      // 이미지인 경우 원본 이미지 표시
      const imageUrl = chunk.image_url || chunk.download_url || `/api/v1/documents/${documentId}/download`;
      console.log('🖼️ 이미지 렌더링:', { chunk, imageUrl, documentId });

      return (
        <div className="mt-2">
          <img
            src={imageUrl}
            alt={title}
            className="max-w-full h-auto max-h-48 rounded-lg border border-gray-200 shadow-sm"
            onLoad={() => {
              console.log('✅ 이미지 로드 성공:', imageUrl);
            }}
            onError={(e) => {
              console.error('❌ 이미지 로드 실패:', imageUrl);
              // 이미지 로드 실패 시 대체 UI 표시
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent) {
                parent.innerHTML = `
                  <div class="flex items-center gap-2 p-4 bg-gray-50 rounded-lg">
                    <div class="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
                      <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                      </svg>
                    </div>
                    <span class="text-gray-600 text-sm">이미지를 불러올 수 없습니다</span>
                  </div>
                `;
              }
            }}
          />
        </div>
      );
    } else if (['xlsx', 'xls', 'csv'].includes(ext || '')) {
      // Excel인 경우 테이블 형태로 표시
      try {
        const lines = chunk.content_preview.split('\n').slice(0, 1); // 첫 번째 행만
        return (
          <div className="bg-gray-50 rounded p-2 text-xs font-mono">
            <div className="flex items-center gap-1 mb-1">
              <Table size={12} className="text-green-500" />
              <span className="text-gray-600">Excel 데이터</span>
            </div>
            <div className="text-gray-700 truncate">
              {lines[0] || '데이터 없음'}
            </div>
          </div>
        );
      } catch {
        return <span className="text-gray-600 text-xs">Excel 데이터 참조</span>;
      }
    } else {
      // 일반 텍스트인 경우
      return (
        <div className="text-gray-700 text-sm line-clamp-1">
          {chunk.content_preview}
        </div>
      );
    }
  };


  // 이미지 파일인지 확인
  const isImageFile = () => {
    const ext = filename.toLowerCase().split('.').pop();
    return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {getFileIcon()}
          <button
            onClick={() => setShowPreview(true)}
            className="font-medium text-gray-900 hover:text-blue-600 truncate text-left"
            title={title}
          >
            {title}
          </button>
          {!isImageFile() && (
            <span className="text-gray-500 text-xs">({chunks.length}개 청크)</span>
          )}
        </div>
        {!isImageFile() && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {/* 이미지 파일인 경우 바로 이미지 표시 */}
      {isImageFile() && chunks.length > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">
              유사도: {(parseFloat(chunks[0].score) * 100).toFixed(1)}%
            </span>
          </div>
          {renderChunkPreview(chunks[0])}
        </div>
      )}

      {/* 일반 파일인 경우 청크 정보 표시 */}
      {!isImageFile() && isExpanded && (
        <div className="mt-3 space-y-2">
          {chunks.map((chunk, index) => (
            <div key={chunk.index} className="border-l-2 border-gray-200 pl-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-500">
                  청크 {parseInt(chunk.chunk_index) + 1} • 유사도: {(parseFloat(chunk.score) * 100).toFixed(1)}%
                </span>
              </div>
              {renderChunkPreview(chunk)}
            </div>
          ))}
        </div>
      )}

      {/* 문서 미리보기 모달 */}
      <DocumentPreviewModal
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        documentId={documentId}
        filename={filename}
      />
    </div>
  );
}

export interface ChatMessageProps {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  sources?: Source[];
  feedback?: 'up' | 'down' | null;
  isStreaming?: boolean;
  onFeedback?: (messageId: string, feedback: 'up' | 'down', comment?: string) => void;
}

export default function ChatMessage({
  id,
  content,
  isUser,
  timestamp,
  sources = [],
  feedback,
  isStreaming = false,
  onFeedback
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [showFeedbackComment, setShowFeedbackComment] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState('');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const handleFeedback = (type: 'up' | 'down') => {
    if (type === 'down') {
      setShowFeedbackComment(true);
    } else {
      onFeedback?.(id, type);
    }
  };

  const submitFeedback = () => {
    onFeedback?.(id, 'down', feedbackComment);
    setShowFeedbackComment(false);
    setFeedbackComment('');
  };

  return (
    <div className={`flex gap-4 p-4 ${isUser ? 'bg-transparent' : 'bg-gray-50'}`}>
      {/* 아바타 - 모든 메시지 좌측 정렬 */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-blue-600 text-white' : 'bg-green-600 text-white'}`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* 메시지 내용 */}
      <div className="flex-1 min-w-0">
        {/* 메시지 텍스트 */}
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-gray-900">
            {content}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-gray-900 ml-1 animate-pulse" />
            )}
          </div>
        </div>

        {/* 출처 정보 (AI 메시지에만 표시) */}
        {!isUser && sources.length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <FileText size={14} />
              참고한 문서 ({sources.length}개)
            </h4>
            <div className="space-y-2">
              {Object.entries(
                sources.reduce((acc, source) => {
                  const key = source.document_id;
                  if (!acc[key]) {
                    acc[key] = {
                      title: source.title,
                      filename: source.filename,
                      chunks: []
                    };
                  }
                  acc[key].chunks.push(source);
                  return acc;
                }, {} as Record<string, { title: string; filename: string; chunks: Source[] }>)
              ).map(([docId, docInfo]) => (
                <DocumentSourceCard
                  key={docId}
                  documentId={docId}
                  title={docInfo.title}
                  filename={docInfo.filename}
                  chunks={docInfo.chunks}
                />
              ))}
            </div>
          </div>
        )}

        {/* 메시지 액션 */}
        <div className="flex items-center justify-between mt-3">
          <div className="text-xs text-gray-500">
            {format(timestamp, 'M월 d일 HH:mm', { locale: ko })}
          </div>

          <div className="flex items-center gap-2">
            {/* 복사 버튼 */}
            <button
              onClick={handleCopy}
              className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
              title="복사"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>

            {/* 피드백 버튼 (AI 메시지에만) */}
            {!isUser && onFeedback && (
              <>
                <button
                  onClick={() => handleFeedback('up')}
                  className={`p-1 rounded transition-colors ${feedback === 'up'
                    ? 'text-green-600 bg-green-50'
                    : 'text-gray-500 hover:text-green-600 hover:bg-green-50'
                    }`}
                  title="좋아요"
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  onClick={() => handleFeedback('down')}
                  className={`p-1 rounded transition-colors ${feedback === 'down'
                    ? 'text-red-600 bg-red-50'
                    : 'text-gray-500 hover:text-red-600 hover:bg-red-50'
                    }`}
                  title="싫어요"
                >
                  <ThumbsDown size={14} />
                </button>
              </>
            )}
          </div>
        </div>

        {/* 피드백 코멘트 입력 모달 (AI 메시지에만) */}
        {!isUser && showFeedbackComment && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="text-sm font-medium text-gray-900 mb-2">
              어떤 부분이 도움이 되지 않았나요?
            </div>
            <textarea
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="피드백을 남겨주세요..."
              className="w-full text-sm border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={() => setShowFeedbackComment(false)}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                취소
              </button>
              <button
                onClick={submitFeedback}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                제출
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
