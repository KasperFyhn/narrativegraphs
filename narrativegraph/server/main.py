import logging
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from narrativegraph.server.routes.graph import router as graph_router
from narrativegraph.server.routes.entities import router as entities_router
from narrativegraph.server.routes.relations import router as relations_router
from narrativegraph.server.routes.docs import router as docs_router

import os

from narrativegraph.db.service import DbService

app = FastAPI()

# Add the CORS middleware to allow all origins for development purposes
app.add_middleware(
    CORSMiddleware,  # noqa, PyCharm bug: https://github.com/fastapi/fastapi/discussions/10968
    allow_origins=["*"],  # You can specify specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure the correct path to your build directory
build_directory = Path(os.path.dirname(__file__)) / "../../visualizer/build/"
if not os.path.isdir(build_directory):
    raise ValueError(f"Build directory '{build_directory}' does not exist.")

# Mount the static files at the root URL
app.mount("/vis", StaticFiles(directory=build_directory, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    if hasattr(app.state, "db_service") and app.state.db_service is not None:
        logging.info("Database service provided to state before startup.")
    elif os.environ.get("DB_PATH") is not None:
        app.state.db_service = DbService(os.environ["DB_PATH"])
        logging.info("Database service initialized from environment variable.")
    else:
        raise ValueError("No database service provided. Set environment variable DB_PATH.")



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"{request}: {exc_str}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)



# @app.get("/")
# async def root():
#     return RedirectResponse(url="/vis")

app.include_router(graph_router, prefix="/graph", tags=["Graph"])
app.include_router(docs_router, prefix="/docs", tags=["Docs"])
app.include_router(entities_router, prefix="/entities", tags=["Entities"])
app.include_router(relations_router, prefix="/relations", tags=["Relations"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("narrativegraph.server.main:app", host="0.0.0.0", port=8001, reload=True)