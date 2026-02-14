import os 
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("MONGODB_NAME", "archestra_mcp")