from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from dotenv import load_dotenv
import database

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on application startup
    database.init_db()
    yield

app = FastAPI(title="Foothold API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Using reload=True so you don't have to restart the server on every save
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)