# Server Layer

This guide provides an overview of the server layer in `narrativegraphs/server/`.

## Overview

The server layer provides a FastAPI-based REST API for querying narrative graph data, plus a built-in visualization frontend.

## Components

| Component               | Purpose                                                             |
| ----------------------- | ------------------------------------------------------------------- |
| **app.py**              | FastAPI application with lifespan management and route registration |
| **backgroundserver.py** | Utility for running the server in notebooks or background           |
| **requests.py**         | Pydantic request models for API endpoints                           |
| **routes/**             | API route handlers organized by entity type                         |
| **static/**             | Pre-built frontend visualization assets                             |

## FastAPI Application (`app.py`)

The main application handles:

- Database engine initialization (from `DB_PATH` env var or provided engine)
- QueryService instantiation for all routes
- CORS middleware configuration
- Static file serving for the visualization frontend
- Custom exception handling for `EntryNotFoundError`

### Running the Server

**Standalone:**

```python
# Set DB_PATH environment variable, then:
uvicorn narrativegraphs.server.app:app --host localhost --port 8001
```

**In notebooks:**

```python
from narrativegraphs.server import BackgroundServer

server = BackgroundServer(db_engine, port=8001)
server.start()  # blocking
# or
server.start(block=False)  # background
server.show_iframe()  # display in notebook
```

## API Routes

Routes are organized by entity type in the `routes/` directory:

| Router            | Prefix           | Purpose                                    |
| ----------------- | ---------------- | ------------------------------------------ |
| **graph**         | `/graph`         | Graph queries, bounds, community detection |
| **entities**      | `/entities`      | Entity lookup, search, related documents   |
| **documents**     | `/docs`          | Document retrieval                         |
| **relations**     | `/relations`     | Relation lookup and related documents      |
| **cooccurrences** | `/cooccurrences` | Cooccurrence lookup and related documents  |

All routes use the shared `QueryService` via FastAPI dependency injection. See the route files for current endpoint details.

## BackgroundServer

Utility class for running the server programmatically:

- Supports blocking and non-blocking modes
- Graceful shutdown handling
- `show_iframe()` for Jupyter notebook display

## Static Frontend

The `static/` directory contains pre-built frontend assets (React app) that provide:

- Interactive graph visualization
- Entity/relation exploration
- Document viewer with highlighted annotations
- Filtering controls

The frontend is served at the root URL when the server is running.

## Architecture Diagram

```
FastAPI App (app.py)
    │
    ├── Lifespan: Initialize DB engine + QueryService
    │
    ├── Middleware: CORS
    │
    ├── Routes (routes/)
    │   ├── graph ──────► GraphService
    │   ├── entities ───► EntityService
    │   ├── documents ──► DocService
    │   ├── relations ──► RelationService
    │   └── cooccurrences ► CooccurrenceService
    │
    └── Static Files: Frontend visualization

BackgroundServer
    │
    └── Wraps FastAPI app for notebook/background usage
```
