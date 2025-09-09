#!/bin/bash
# MinIO 초기화 및 CORS 설정 스크립트

# MinIO 서버가 시작될 때까지 대기
echo "Waiting for MinIO server to start..."
until mc alias set myminio http://minio:9000 minioadmin minioadmin; do
    echo "MinIO not ready, waiting..."
    sleep 2
done

echo "MinIO server is ready!"

# 버킷 생성 (이미 존재하면 무시)
mc mb myminio/company-on-documents --ignore-existing
echo "Bucket created or already exists"

# 공개 읽기 권한 설정
mc anonymous set public myminio/company-on-documents
echo "Public access configured"

# CORS 설정을 위한 XML 파일 생성
cat > /tmp/cors.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration>
    <CORSRule>
        <AllowedOrigin>*</AllowedOrigin>
        <AllowedMethod>GET</AllowedMethod>
        <AllowedMethod>PUT</AllowedMethod>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedMethod>DELETE</AllowedMethod>
        <AllowedMethod>HEAD</AllowedMethod>
        <AllowedHeader>*</AllowedHeader>
        <ExposeHeader>ETag</ExposeHeader>
        <MaxAgeSeconds>3000</MaxAgeSeconds>
    </CORSRule>
</CORSConfiguration>
EOF

# CORS 설정 적용 시도
echo "Setting CORS configuration..."
if mc cors set myminio/company-on-documents /tmp/cors.xml; then
    echo "CORS configuration applied successfully"
else
    echo "Failed to set CORS configuration, but continuing..."
fi

echo "MinIO initialization completed"
