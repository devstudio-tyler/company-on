import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'Company-on',
    description: 'AI 기반 문서 검색과 채팅으로 내부 지식을 쉽게 찾아보세요',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="ko">
            <head>
                <link rel="preconnect" href="https://cdn.jsdelivr.net" />
                <link
                    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
                    rel="stylesheet"
                />
            </head>
            <body className="font-pretendard">{children}</body>
        </html>
    )
}

