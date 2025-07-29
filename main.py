from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from api.router import router


app = FastAPI()

app.include_router(router, prefix="/api")

@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")