import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from narrativegraphs.db.engine import get_engine, get_session_factory
from narrativegraphs.errors import EntryNotFoundError
from narrativegraphs.server.routes.cooccurrences import router as cooccurrences_router
from narrativegraphs.server.routes.documents import router as docs_router
from narrativegraphs.server.routes.entities import router as entities_router
from narrativegraphs.server.routes.graph import router as graph_router
from narrativegraphs.server.routes.relations import router as relations_router
from narrativegraphs.service import QueryService

build_directory = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app_arg: FastAPI):
    # Ensure DB path is set
    if hasattr(app_arg.state, "db_engine") and app_arg.state.db_engine is not None:
        logging.info("Database engine provided to state before startup.")
    elif os.environ.get("DB_PATH") is not None:
        app_arg.state.db_engine = get_engine(os.environ["DB_PATH"])
        logging.info("Database engine initialized from environment variable.")
    else:
        raise ValueError(
            "No database engine provided. Set environment variable DB_PATH."
        )
    app_arg.state.create_session = get_session_factory(app_arg.state.db_engine)
    app_arg.state.query_service = QueryService(engine=app_arg.state.db_engine)

    if not os.path.isdir(build_directory):
        raise ValueError(f"Build directory '{build_directory}' does not exist.")
    app_arg.mount("", StaticFiles(directory=build_directory, html=True), name="static")

    yield


app = FastAPI(lifespan=lifespan)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # specify specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EntryNotFoundError)
async def entry_not_found(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(graph_router, prefix="/graph", tags=["Graph"])
app.include_router(docs_router, prefix="/docs", tags=["Docs"])
app.include_router(entities_router, prefix="/entities", tags=["Entities"])
app.include_router(
    cooccurrences_router, prefix="/cooccurrences", tags=["Cooccurrences"]
)
app.include_router(relations_router, prefix="/relations", tags=["Relations"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "narrativegraphs.server.app:app", host="localhost", port=8001, reload=True
    )
