from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from api.router import router
from fastapi.staticfiles import StaticFiles
from core.logging_config import setup_logging
import os
from datetime import datetime

# Setup logging
os.makedirs('logs', exist_ok=True)
setup_logging()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router, prefix="/api")

@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")