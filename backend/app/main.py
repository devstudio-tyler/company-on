from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAGbot API",
    description="RAG-based AI chatbot for internal document search",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RAGbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}

