import uvicorn
from src.application.factory import create_app
from src.core import settings

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.local.host,
        port=settings.local.port,
        workers=settings.local.workers,
        reload=True,
    )
