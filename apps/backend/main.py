from fastapi import FastAPI

app = FastAPI(title="Boxless Backend", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Welcome to Boxless Backend"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
