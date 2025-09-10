'use client';

import ChatPage from '@/components/chat/ChatPage';
import Layout from '@/components/layout/Layout';

export default function Home() {
    return (
        <Layout>
            {({ currentSessionId }) => (
                <ChatPage sessionId={currentSessionId} />
            )}
        </Layout>
    );
}

