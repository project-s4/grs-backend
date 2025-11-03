from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import complaints, departments, ai, auth, admin, ai_chat, ai_audio

# Load environment variables
load_dotenv()

app = FastAPI(title="Grievance Redressal Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api", tags=["Complaints"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/internal", tags=["AI-Service"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["AI Chat"])
app.include_router(ai_audio.router, prefix="/api/ai/audio", tags=["AI Audio"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
