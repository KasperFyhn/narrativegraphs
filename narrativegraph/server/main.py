from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

import os

app = FastAPI()

# Ensure the correct path to your build directory
build_directory = Path(os.path.dirname(__file__)) / "../../visualizer/build/"
if not os.path.isdir(build_directory):
    raise ValueError(f"Build directory '{build_directory}' does not exist.")

# Mount the static files at the root URL
app.mount("/vis", StaticFiles(directory=build_directory, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    db_path = os.getenv('DB_PATH', None)
    # Here you would initialize your database connection with `db_path`
    print(f"Database path: {db_path}")

@app.get("/")
async def root():
    return RedirectResponse(url="/vis")

@app.get("/hello_world")
def hello_world():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)