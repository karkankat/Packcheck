"""PackCheck - сервис проверки снаряжения для велопохода.
Учебная основа: app_final.py из материалов курса.
"""

from fastapi import FastAPI

APP_VERSION = "0.1.0"

app = FastAPI(title="PackCheck", version=APP_VERSION)

@app.get("/")
def root():
    return{
        "message": "PackCheck работает",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return{"status": "ok"}

@app.get("/version")
def version():
    return{"sversion": APP_VERSION}