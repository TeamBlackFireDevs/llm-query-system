from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your modules
from config import settings
from api.endpoints import router

# Create FastAPI app
app = FastAPI(
    title="LLM-Powered Query-Retrieval System",
    description="Serverless document processing system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "LLM Query-Retrieval System",
        "status": "running on Vercel",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "platform": "vercel"}

# For Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
