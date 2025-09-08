/** @type {import('next').NextConfig} */
const nextConfig = {
    // 성능 최적화 설정 (Next.js 15 호환)
    compress: true,

    // 이미지 최적화
    images: {
        formats: ['image/webp', 'image/avif'],
        minimumCacheTTL: 60,
    },

    // 번들 분석기 (개발 시에만)
    ...(process.env.ANALYZE === 'true' && {
        webpack: (config) => {
            config.plugins.push(
                new (require('webpack-bundle-analyzer').BundleAnalyzerPlugin)({
                    analyzerMode: 'server',
                    openAnalyzer: true,
                })
            )
            return config
        },
    }),

    // 실험적 기능
    experimental: {
        optimizePackageImports: ['lucide-react'],
    },

    // 컴파일러 최적화
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production',
    },

    // API 프록시 설정 (백엔드로 요청 전달)
    async rewrites() {
        return [
            {
                source: '/api/v1/:path*',
                destination: 'http://localhost:8000/api/v1/:path*',
            },
        ];
    },
}

module.exports = nextConfig

