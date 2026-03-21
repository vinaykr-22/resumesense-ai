import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    auto_seed = os.getenv("AUTO_SEED_JOBS", "false").lower() in ("1", "true", "yes")
    if not auto_seed:
        yield
        return

    try:
        logger.info("Running startup tasks...")
        from jobs_dataset.seed_embeddings import seed_jobs
        seed_jobs()
        logger.info("Startup tasks complete.")
    except Exception as e:
        logger.warning(f"Startup task failed (non-fatal): {e}")
        # Do NOT re-raise — server must start regardless
    yield

app = FastAPI(title="FastAPI Backend", lifespan=lifespan)

# CORS configuration (temporary: allow all origins for debugging)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
import logging
from logging.handlers import TimedRotatingFileHandler
import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# Rotate logs daily, keep for 7 days
log_handler = TimedRotatingFileHandler("logs/app.log", when="midnight", interval=1, backupCount=7)
log_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
# Also output to console for easy debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Try to extract user email if token exists (lightweight check just for logging)
    user_email = "anonymous"
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from jose import jwt
            token = auth_header.split(" ")[1]
            JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_here")
            JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            user_email = payload.get("sub", "anonymous")
        except Exception:
            pass

    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        process_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"{request.method} {request.url.path} {status_code} {process_time_ms}ms {user_email}")
        
    return response

# Global Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": str(exc), "type": "validation_error"}
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Don't catch HTTPExceptions which are intentionally thrown by FastAPI/us
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
        
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    detail_msg = f"Internal server error: {str(exc)}" if os.getenv("DEBUG", "False").lower() in ("true", "1") else "Contact support"
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": detail_msg}
    )

# API Router with prefix /api/v1
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

from services.llm_provider import llm

@api_router.get("/health/llm")
async def llm_health_check():
    try:
        result = await llm.complete("Say hello in exactly three words.")
        return {
            "provider": llm.provider,
            "model": getattr(llm, 'openai_model', 'unknown'),
            "response": result,
            "ok": True
        }
    except Exception as e:
        import traceback
        return {
            "provider": llm.provider,
            "model": getattr(llm, 'openai_model', 'unknown'),
            "has_openai_key": bool(llm.openai_api_key),
            "openai_key_prefix": llm.openai_api_key[:12] + "..." if llm.openai_api_key else None,
            "error_type": type(e).__name__,
            "error": str(e),
            "traceback": traceback.format_exc()[-500:],
            "ok": False
        }

from routes import auth_routes, resume_routes, job_routes
api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
api_router.include_router(resume_routes.router, prefix="/resume", tags=["resume"])
api_router.include_router(job_routes.router, prefix="/jobs", tags=["jobs"])

# Register the main wrapper router
app.include_router(api_router)



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
