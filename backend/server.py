from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    model_provider: str
    model_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_safe: bool = True

class ChatMessageCreate(BaseModel):
    session_id: str
    message: str
    model_provider: str = "openai"
    model_name: str = "gpt-5"

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_messages: int = 0

class ChatSessionCreate(BaseModel):
    session_name: str


def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key in ['timestamp', 'created_at'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
    return item

def is_content_safe_for_kids(message: str, response: str) -> bool:
    """Basic content safety check for kids aged 8-12"""
    unsafe_keywords = [
        'violence', 'weapon', 'kill', 'death', 'blood', 'war', 'fight',
        'inappropriate', 'adult', 'mature', 'scary', 'horror', 'fear',
        'hate', 'racism', 'discrimination', 'bullying', 'mean'
    ]
    
    combined_text = (message + " " + response).lower()
    return not any(keyword in combined_text for keyword in unsafe_keywords)

def make_kid_friendly(response: str) -> str:
    """Make AI response more suitable for kids aged 8-12"""
    # Replace complex words with simpler alternatives
    replacements = {
        'artificial intelligence': 'AI (like a smart computer)',
        'algorithm': 'computer instructions',
        'machine learning': 'how computers learn',
        'neural network': 'computer brain',
        'processing': 'thinking',
        'generate': 'create',
        'sophisticated': 'smart',
        'complexity': 'how hard something is',
        'analyze': 'look at carefully',
        'implement': 'make it work'
    }
    
    result = response
    for complex_word, simple_word in replacements.items():
        result = result.replace(complex_word, simple_word)
    
    return result

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Welcome to AI Learning Platform for Kids!"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    status_data = prepare_for_mongo(status_obj.dict())
    _ = await db.status_checks.insert_one(status_data)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**parse_from_mongo(status_check)) for status_check in status_checks]

@api_router.post("/chat/session", response_model=ChatSession)
async def create_chat_session(input: ChatSessionCreate):
    session_obj = ChatSession(**input.dict())
    session_data = prepare_for_mongo(session_obj.dict())
    await db.chat_sessions.insert_one(session_data)
    return session_obj

@api_router.get("/chat/sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    sessions = await db.chat_sessions.find().to_list(100)
    return [ChatSession(**parse_from_mongo(session)) for session in sessions]

@api_router.post("/chat/message", response_model=ChatMessage)
async def send_chat_message(input: ChatMessageCreate):
    try:
        # Get the EMERGENT_LLM_KEY from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create kid-friendly system message
        system_message = """You are a friendly AI teacher helping kids aged 8-12 learn about artificial intelligence and how computers work. 
        
        Rules:
        1. Use simple, fun language that kids can understand
        2. Keep explanations short and engaging
        3. Use examples from everyday life (toys, games, school)
        4. Always be encouraging and positive
        5. If asked about something not suitable for kids, gently redirect to learning topics
        6. Make AI concepts sound exciting and magical but also explain them simply
        7. Use emojis occasionally to make responses fun
        
        Remember: You're teaching kids about AI, so make it fun and easy to understand!"""
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=api_key,
            session_id=input.session_id,
            system_message=system_message
        ).with_model(input.model_provider, input.model_name)
        
        # Create user message
        user_message = UserMessage(text=input.message)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)
        
        # Make response kid-friendly
        kid_friendly_response = make_kid_friendly(ai_response)
        
        # Check content safety
        is_safe = is_content_safe_for_kids(input.message, kid_friendly_response)
        
        if not is_safe:
            kid_friendly_response = "Let's talk about something more fun! How about we explore how AI helps create cool games or helps robots move around? 🤖"
        
        # Create chat message object
        chat_message = ChatMessage(
            session_id=input.session_id,
            message=input.message,
            response=kid_friendly_response,
            model_provider=input.model_provider,
            model_name=input.model_name,
            is_safe=is_safe
        )
        
        # Save to database
        message_data = prepare_for_mongo(chat_message.dict())
        await db.chat_messages.insert_one(message_data)
        
        # Update session message count
        await db.chat_sessions.update_one(
            {"id": input.session_id},
            {"$inc": {"total_messages": 1}}
        )
        
        return chat_message
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

@api_router.get("/chat/messages/{session_id}", response_model=List[ChatMessage])
async def get_chat_messages(session_id: str):
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**parse_from_mongo(message)) for message in messages]

@api_router.get("/models")
async def get_available_models():
    return {
        "models": [
            {
                "provider": "openai",
                "name": "gpt-5",
                "display_name": "GPT-5 (Super Smart)",
                "description": "The newest and smartest AI that can help with almost anything!",
                "kid_friendly_description": "Like having a really smart friend who knows lots of cool facts! 🧠"
            },
            {
                "provider": "anthropic", 
                "name": "claude-4-sonnet-20250514",
                "display_name": "Claude 4 (Creative Helper)",
                "description": "Great at creative writing and explaining things in fun ways!",
                "kid_friendly_description": "Loves to tell stories and explain things with fun examples! 📚"
            },
            {
                "provider": "gemini",
                "name": "gemini-2.5-pro", 
                "display_name": "Gemini 2.5 (Multi-Talented)",
                "description": "Can do many different things and is great at problem-solving!",
                "kid_friendly_description": "Like a super helper that can do lots of different tasks! ⭐"
            }
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()