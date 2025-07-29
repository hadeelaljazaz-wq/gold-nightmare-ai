from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import logging
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import bot modules
from gold_bot.bot import GoldNightmareBot

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gold_nightmare_bot')]

# Initialize FastAPI
app = FastAPI(title="Gold Nightmare Bot API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Initialize Bot
bot_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize the bot on startup"""
    global bot_instance
    try:
        bot_instance = GoldNightmareBot()
        await bot_instance.initialize()
        
        # Start bot in background task
        asyncio.create_task(bot_instance.start())
        
        logging.info("🚀 Gold Nightmare Bot started successfully!")
        
    except Exception as e:
        logging.error(f"❌ Failed to start bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bot_instance
    if bot_instance:
        await bot_instance.stop()
    client.close()

# Health check endpoints
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bot_running": bot_instance is not None and bot_instance.is_running() if bot_instance else False,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/bot/stats")
async def get_bot_stats():
    """Get bot statistics"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    stats = await bot_instance.get_stats()
    return stats

@api_router.post("/bot/broadcast")
async def broadcast_message(request: dict):
    """Admin endpoint to broadcast messages"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    message = request.get("message")
    admin_id = request.get("admin_id")
    
    if not message or not admin_id:
        raise HTTPException(status_code=400, detail="Message and admin_id required")
    
    # Verify admin permissions
    if str(admin_id) != os.environ.get('MASTER_USER_ID'):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await bot_instance.broadcast_message(message)
    return {"status": "success", "sent_count": result}

# Include API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/supervisor/gold_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)