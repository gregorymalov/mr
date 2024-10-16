from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.api_routes import router
from routers.api_routes import initialize_blockchain

app = FastAPI(title="MRx0", version="0.0.2")
app.include_router(router, tags=["Blockchain"], prefix="/blockchain")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await initialize_blockchain()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True, lifespan="on")