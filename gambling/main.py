from fastapi import FastAPI
from routes.usuario import router_usuario

app = FastAPI()

app.include_router(router_usuario)
