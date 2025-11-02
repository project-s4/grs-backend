from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import complaints, departments, ai, auth, admin

# Load environment variables
load_dotenv()

app = FastAPI(title="Grievance Redressal Backend")

app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api", tags=["Complaints"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/internal", tags=["AI-Service"])
