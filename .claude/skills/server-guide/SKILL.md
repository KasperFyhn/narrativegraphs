---
name: server-guide
description: Overview of the FastAPI server and REST API
user-invocable: false
---

# Server Layer Guide

Overview of the server layer in `narrativegraphs/server/`.

## Components

| Component               | Purpose                                                 |
| ----------------------- | ------------------------------------------------------- |
| **app.py**              | FastAPI application with routes and static file serving |
| **backgroundserver.py** | Run server in notebooks or background                   |
| **requests.py**         | Pydantic request models                                 |
| **routes/**             | API endpoint handlers by entity type                    |
| **static/**             | Frontend visualization assets                           |

## Running the Server

**Standalone:** Set `DB_PATH` env var, run with uvicorn

**In notebooks:**

```python
from narrativegraphs.server import BackgroundServer
server = BackgroundServer(db_engine, port=8001)
server.start()
```

## Route Organization

| Router        | Prefix           | Service             |
| ------------- | ---------------- | ------------------- |
| graph         | `/graph`         | GraphService        |
| entities      | `/entities`      | EntityService       |
| documents     | `/docs`          | DocService          |
| relations     | `/relations`     | RelationService     |
| cooccurrences | `/cooccurrences` | CooccurrenceService |

All routes use `QueryService` via dependency injection.

## Architecture

```
FastAPI App
    ├── Lifespan: DB engine + QueryService init
    ├── Routes (routes/) → QueryService sub-services
    └── Static Files → Frontend visualization

BackgroundServer → Wraps app for notebook usage
```
