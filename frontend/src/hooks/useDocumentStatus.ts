import { useEffect, useRef } from 'react';

interface DocumentStatusUpdate {
    upload_id: string;
    filename: string;
    status: string;
    progress_percentage: number;
    uploaded_size: number;
    file_size: number;
    document_id?: number;
    error_message?: string;
    updated_at: string;
}

interface UseDocumentStatusProps {
    uploadId?: string;
    onStatusUpdate: (status: DocumentStatusUpdate) => void;
    enabled?: boolean;
}

export function useDocumentStatus({
    uploadId,
    onStatusUpdate,
    enabled = true
}: UseDocumentStatusProps) {
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        if (!uploadId || !enabled) {
            return;
        }

        // SSE 연결 설정
        const eventSource = new EventSource(`/api/v1/uploads/sessions/${encodeURIComponent(uploadId)}/stream`);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            console.log(`SSE connected for upload: ${uploadId}`);
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as DocumentStatusUpdate;
                onStatusUpdate(data);

                // 완료 상태이면 연결 종료
                if (data.status === 'completed' || data.status === 'failed') {
                    eventSource.close();
                }
            } catch (error) {
                console.error('SSE 메시지 파싱 오류:', error);
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE 연결 오류:', error);
            eventSource.close();
        };

        return () => {
            if (eventSource.readyState !== EventSource.CLOSED) {
                eventSource.close();
            }
        };
    }, [uploadId, enabled, onStatusUpdate]);

    const disconnect = () => {
        if (eventSourceRef.current && eventSourceRef.current.readyState !== EventSource.CLOSED) {
            eventSourceRef.current.close();
        }
    };

    return { disconnect };
}
