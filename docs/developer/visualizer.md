# Visualizer Frontend

This guide provides an overview of the visualizer in `visualizer/`.

## Overview

A React/TypeScript single-page application that provides interactive visualization of narrative graphs. Built with Create React App and uses react-graph-vis for graph rendering.

## Project Structure

```
visualizer/
├── src/
│   ├── components/     # React components
│   ├── contexts/       # React context providers
│   ├── hooks/          # Custom React hooks
│   ├── reducers/       # State reducers
│   ├── services/       # API client services
│   └── types/          # TypeScript type definitions
├── public/             # Static assets
└── build/              # Production build output
```

## Architecture

### Context Providers

The app uses React Context for state management, nested in this order:

| Context                 | Purpose                                             |
| ----------------------- | --------------------------------------------------- |
| **ServiceContext**      | API service instances (graph, docs, entities, etc.) |
| **GraphOptionsContext** | Visualization options (layout, styling)             |
| **GraphQueryContext**   | Current query state and filters                     |
| **SelectionContext**    | Currently selected nodes/edges                      |

### Services (`services/`)

Client-side services that mirror the backend API:

| Service             | Backend Route    |
| ------------------- | ---------------- |
| GraphService        | `/graph`         |
| DocService          | `/docs`          |
| EntityService       | `/entities`      |
| RelationService     | `/relations`     |
| CooccurrenceService | `/cooccurrences` |

Services auto-detect the API URL based on environment (localhost dev vs production).

### Components (`components/`)

| Directory      | Purpose                                              |
| -------------- | ---------------------------------------------------- |
| **graph/**     | Main graph viewer, sidebar, controls                 |
| **inspector/** | Detail panels for selected items (docs, entity info) |
| **common/**    | Shared UI components (panels, entity chips, inputs)  |

### Reducers (`reducers/`)

Complex state management for:

- Graph filter state
- Graph query state
- Navigation history

## Development

```bash
cd visualizer
npm install
npm start        # Dev server on port 3000
npm run build    # Production build
```

The dev server proxies API requests to `localhost:8001` (the backend).

## Deployment

The production build (`npm run build`) outputs to `build/`, which is copied to `narrativegraphs/server/static/` to be served by the FastAPI backend.

## Key Dependencies

- **react-graph-vis** - Graph visualization
- **react-router-dom** - Client-side routing
- **lucide-react** - Icons
- **draft-js** - Rich text editing (for document display)
