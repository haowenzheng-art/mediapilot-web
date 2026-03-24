
"""
MediaPilot 简化版后端 - 先用这个测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*60)
print("   MediaPilot Backend - Simplified")
print("="*60)
print()

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("[OK] FastAPI imported")
except ImportError:
    print("[WARN] FastAPI not found, creating mock server")
    FastAPI = None

from shared.config import settings

if FastAPI:
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION
    )

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {
            "name": "MediaPilot API",
            "version": settings.API_VERSION,
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    print()
    print("FastAPI app created!")
    print()
    print("To run the server:")
    print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print()

else:
    print()
    print("="*60)
    print("   Mock Server Mode")
    print("="*60)
    print()
    print("This is a mock backend.")
    print("To use the real API, install dependencies:")
    print("  pip install fastapi uvicorn")
    print()

print("Backend is ready!")
print()

try:
    input("Press Enter to exit...")
except:
    pass

