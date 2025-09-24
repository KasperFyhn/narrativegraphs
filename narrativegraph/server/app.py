import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from narrativegraph.db.engine import get_engine, get_session_factory
from narrativegraph.errors import EntryNotFoundError
from narrativegraph.server.routes.documents import router as docs_router
from narrativegraph.server.routes.entities import router as entities_router
from narrativegraph.server.routes.graph import router as graph_router
from narrativegraph.server.routes.relations import router as relations_router
from narrativegraph.service import QueryService


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

    # Ensure the correct path to your build directory
    build_directory = Path(os.path.dirname(__file__)) / "../../visualizer/build/"
    if not os.path.isdir(build_directory):
        raise ValueError(f"Build directory '{build_directory}' does not exist.")
    app_arg.mount(
        "/vis", StaticFiles(directory=build_directory, html=True), name="static"
    )

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # noqa, PyCharm bug: https://github.com/fastapi/fastapi/discussions/10968
    allow_origins=["*"],  # specify specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/vis")


@app.exception_handler(EntryNotFoundError)
async def entry_not_found(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(graph_router, prefix="/graph", tags=["Graph"])
app.include_router(docs_router, prefix="/docs", tags=["Docs"])
app.include_router(entities_router, prefix="/entities", tags=["Entities"])
app.include_router(relations_router, prefix="/relations", tags=["Relations"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("narrativegraph.server.app:app", host="0.0.0.0", port=8001, reload=True)
