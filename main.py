from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from api.router import router
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router, prefix="/api")

@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")