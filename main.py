from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import stt, prosody, chat, scenario

app = FastAPI(
    title="Korrect API",
    description="고려인 아동 한국어 말하기 학습 플랫폼 백엔드",
    version="1.0.0",
)

# Flutter 앱에서 접근 가능하도록 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stt.router, prefix="/api")
app.include_router(prosody.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(scenario.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Korrect API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
