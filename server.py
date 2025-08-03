import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


def init_signal():
    """使用 ServerSignals 替代 Qt Signal"""
    from mdcx.server.signals import signal
    from mdcx.signals import set_signal

    set_signal(signal)


def create_app() -> FastAPI:
    init_signal()

    from mdcx.server.api.v1 import api
    from mdcx.server.ws.auth import WebSocketProtocolBearerMiddleware

    app = FastAPI(title="MDCx API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    app.add_middleware(WebSocketProtocolBearerMiddleware)

    app.include_router(api)
    app.mount("/", StaticFiles(directory="ui/dist", html=True), name="ui")

    return app


app = create_app()

if __name__ == "__main__":
    from mdcx.server.config import HOST, PORT

    uvicorn.run(app, host=HOST, port=PORT)
