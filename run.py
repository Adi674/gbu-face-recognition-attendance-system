import uvicorn
from fastapi_auth.app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_auth.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )