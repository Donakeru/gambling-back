from fastapi import FastAPI
from routes.usuario import router_usuario
from routes.admin import router_admin

app = FastAPI()

app.include_router(router_usuario)
app.include_router(router_admin)
