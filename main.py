import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


from src.routes import users, plan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    """
    This FastAPI application serves as a web server that provides API endpoints for managing users and plans. It includes CORS (Cross-Origin Resource Sharing) middleware to allow requests from any origin, making it suitable for development and testing purposes.
    
    The script performs the following tasks:
    1. Imports necessary modules and dependencies, including FastAPI, CORS middleware, and your defined routes.
    2. Creates a FastAPI app instance.
    3. Configures CORS middleware to allow cross-origin requests.
    4. Includes routers for the "plan" and "users" routes, which are defined in the imported modules.
    5. Defines a simple root endpoint that returns a greeting message.
    6. Uses Uvicorn to run the FastAPI app on the local server with auto-reloading for development.
    
    Usage:
    - Run this script to start the FastAPI server.
    - Access the API endpoints at http://localhost:8000 or the specified host and port.

    """
    return {"message": "Hi!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", reload=True, log_level="info")
