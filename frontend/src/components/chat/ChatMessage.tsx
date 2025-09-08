'use client';

import React, { useState } from 'react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  Check, 
  ExternalLink,
  FileText,
  MessageCircle,
  User,
  Bot
} from 'lucide-react';

export interface Source {
  index: number;
  title: string;
  filename: string;
  score: number;
  download_url?: string;
  preview_url?: string;
  content_preview: string;
  document_id: number;
  chunk_index: number;
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
      {/* 아바타 */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser 
          ? 'bg-blue-600 text-white' 
          : 'bg-green-600 text-white'
      }`}>
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
              {sources.map((source) => (
                <div
                  key={source.index}
                  className="bg-white border border-gray-200 rounded-lg p-3 text-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 mb-1">
                        {source.title}
                      </div>
                      <div className="text-gray-600 text-xs mb-2">
                        {source.filename} • 유사도: {(source.score * 100).toFixed(1)}%
                      </div>
                      <div className="text-gray-700 line-clamp-2">
                        {source.content_preview}
                      </div>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      {source.preview_url && (
                        <a
                          href={source.preview_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="미리보기"
                        >
                          <MessageCircle size={14} />
                        </a>
                      )}
                      {source.download_url && (
                        <a
                          href={source.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded"
                          title="다운로드"
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
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
            {!isUser && (
              <>
                <button
                  onClick={() => handleFeedback('up')}
                  className={`p-1 rounded transition-colors ${
                    feedback === 'up'
                      ? 'text-green-600 bg-green-50'
                      : 'text-gray-500 hover:text-green-600 hover:bg-green-50'
                  }`}
                  title="좋아요"
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  onClick={() => handleFeedback('down')}
                  className={`p-1 rounded transition-colors ${
                    feedback === 'down'
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

        {/* 피드백 코멘트 입력 모달 */}
        {showFeedbackComment && (
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
