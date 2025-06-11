from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uvicorn
import logging

from pathlib import Path
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


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
  """Serves the index.html"""
  return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# import analytics.endpoints  
# app.include_router(analytics.endpoints.router)

import interviewer.endpoints
app.include_router(interviewer.endpoints.router)

# import payment.endpoints
# app.include_router(payment.endpoints.router)


if __name__ == "__main__":
  try:
    uvicorn.run("service:app", host="127.0.0.1", port=8000, reload=True)
  except KeyboardInterrupt:
    logging.info("Exiting application via KeyboardInterrupt...")
  except Exception as e:
    logging.error(f"Unhandled exception in main: {e}")
    import traceback
    traceback.print_exc()
  