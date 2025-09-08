'use client';

import dynamic from 'next/dynamic';

import { MainContentSkeleton } from '@/components/ui/LoadingSkeleton';

// 컴포넌트들을 동적으로 로드
const Layout = dynamic(() => import('@/components/layout/Layout'), {
    loading: () => <MainContentSkeleton />
});

const ChatPage = dynamic(() => import('@/components/chat/ChatPage'), {
    loading: () => <MainContentSkeleton />
});

export default function Home() {
    return (
        <Layout>
            <ChatPage />
        </Layout>
    );
}

