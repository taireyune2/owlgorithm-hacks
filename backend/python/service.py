from common import configs, logger
logger.setup(configs.file["logging"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
import os
import uvicorn
import logging
import traceback

from pathlib import Path

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

# Set limiter into app state here
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
  return JSONResponse(
      status_code=429,
      content={
          "status": "failure",
          "message": "Too many requests! Please try again later."
      }
  )


if api_configs["dev"]:
  STATIC_DIR = Path(__file__).parent / "static"
  app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

  @app.get("/")
  async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
async def health_check():
  """Health check endpoint."""
  return {"status": "ok", "message": "Service is running."}


# import analytics.endpoints  
# app.include_router(analytics.endpoints.router)

import interviewer.endpoints
app.include_router(interviewer.endpoints.router)

# import payment.endpoints
# app.include_router(payment.endpoints.router)


if __name__ == "__main__":
  try:
    uvicorn.run("service:app", host="0.0.0.0", port=8080)
    #uvicorn.run("service:app", host="localhost", port=8000, reload=True)
  except KeyboardInterrupt:
    logging.info("Exiting application via KeyboardInterrupt...")
  except Exception as e:
    logging.error(f"Unhandled exception in main: {e}")
    traceback.print_exc()
  