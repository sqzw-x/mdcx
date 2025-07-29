import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mdcx.server.api.v1 import api
from mdcx.server.ws.auth import WebSocketProtocolBearerMiddleware

app = FastAPI()
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


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
