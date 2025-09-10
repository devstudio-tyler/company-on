'use client';


interface LoadingSkeletonProps {
    className?: string;
    lines?: number;
}

export default function LoadingSkeleton({ className = '', lines = 1 }: LoadingSkeletonProps) {
    return (
        <div className={`animate-pulse ${className}`}>
            {Array.from({ length: lines }).map((_, index) => (
                <div
                    key={index}
                    className="h-4 bg-gray-200 rounded mb-2"
                    style={{
                        width: `${Math.random() * 40 + 60}%`,
                    }}
                />
            ))}
        </div>
    );
}

// 특정 컴포넌트용 스켈레톤
export function SidebarSkeleton() {
    return (
        <div className="bg-white border-r border-gray-200 w-80 p-4">
            <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded mb-4"></div>
                <div className="h-10 bg-gray-200 rounded mb-4"></div>
                <div className="space-y-2">
                    {Array.from({ length: 3 }).map((_, index) => (
                        <div key={index} className="h-16 bg-gray-200 rounded"></div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function HeaderSkeleton() {
    return (
        <div className="bg-white border-b border-gray-200 px-4 py-3">
            <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            </div>
        </div>
    );
}

export function MainContentSkeleton() {
    return (
        <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 p-6">
            <div className="animate-pulse max-w-4xl mx-auto text-center">
                <div className="h-12 bg-gray-200 rounded mb-4 mx-auto w-1/2"></div>
                <div className="h-6 bg-gray-200 rounded mb-8 mx-auto w-3/4"></div>
                <div className="flex gap-4 justify-center mb-12">
                    <div className="h-12 bg-gray-200 rounded w-32"></div>
                    <div className="h-12 bg-gray-200 rounded w-32"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    {Array.from({ length: 4 }).map((_, index) => (
                        <div key={index} className="h-16 bg-gray-200 rounded"></div>
                    ))}
                </div>
            </div>
        </div>
    );
}

