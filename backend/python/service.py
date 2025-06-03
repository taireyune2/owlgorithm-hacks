from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common import configs

api_configs = configs.file["api"]   
app = FastAPI(
    root_path=api_configs["root_path"],
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=api_configs["cors"],  # Allow specific origins (or use ["*"] for all origins)
    # allow_origins="*",  # Allow specific origins (or use ["*"] for all origins)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods or specify particular methods ["GET", "POST"]
    allow_headers=["*"],  # Allow all headers or specify ["Content-Type", "Authorization"]
)

# import analytics.endpoints  
# app.include_router(analytics.endpoints.router)

import interviewer.endpoints
app.include_router(interviewer.endpoints.router)

# import payment.endpoints
# app.include_router(payment.endpoints.router)