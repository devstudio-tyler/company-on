'use client';

import dynamic from 'next/dynamic';

import { MainContentSkeleton } from '@/components/ui/LoadingSkeleton';

// Layout 컴포넌트를 동적으로 로드
const Layout = dynamic(() => import('@/components/layout/Layout'), {
    loading: () => <MainContentSkeleton />
});

export default function Home() {
    return (
        <Layout>
            <div className="h-full flex flex-col bg-gray-50">
                {/* 채팅 메시지 영역 (추후 메시지 리스트 렌더링) */}
                <div className="flex-1 overflow-y-auto" />

                {/* 하단 입력창 - ChatGPT 스타일 (스크롤 영역 하단 고정) */}
                <div className="border-t bg-white sticky bottom-0">
                    <div className="max-w-3xl mx-auto px-4 py-3">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                const form = e.currentTarget as HTMLFormElement;
                                const input = form.elements.namedItem('prompt') as HTMLInputElement;
                                const prompt = input.value.trim();
                                if (!prompt) return;
                                // TODO: 세션이 없으면 자동 생성 후 메시지 전송
                                console.log('send:', prompt);
                                input.value = '';
                            }}
                            className="relative"
                        >
                            <textarea
                                name="prompt"
                                rows={3}
                                placeholder="무엇이든 질문해보세요..."
                                className="w-full resize-none rounded-2xl border border-gray-300 px-4 py-3 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[72px] max-h-40"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
                                    }
                                }}
                            />
                            <div className="absolute right-2 top-2">
                                <button
                                    type="submit"
                                    className="w-10 h-10 bg-blue-600 text-white rounded-full hover:bg-blue-700 flex items-center justify-center shadow-sm"
                                >
                                    {/* 아이콘 버튼 */}
                                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M22 2L11 13" />
                                        <path d="M22 2l-7 20-4-9-9-4 20-7z" />
                                    </svg>
                                </button>
                            </div>
                        </form>
                        <p className="text-[11px] text-gray-500 mt-2">
                            개인정보나 민감정보를 입력하지 마세요.
                        </p>
                    </div>
                </div>
            </div>
        </Layout>
    );
}

