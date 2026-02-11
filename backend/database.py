import os
import logging
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection
)
from pymongo import ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "autopilot")


class Database:
    """MongoDB Connection Manager"""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    # Collections
    execution_history: Optional[AsyncIOMotorCollection] = None
    patterns: Optional[AsyncIOMotorCollection] = None
    optimization_suggestions: Optional[AsyncIOMotorCollection] = None
    agent_scores: Optional[AsyncIOMotorCollection] = None
    workflows: Optional[AsyncIOMotorCollection] = None
    deployments: Optional[AsyncIOMotorCollection] = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(MONGODB_URL)
        db.db = db.client[MONGODB_DB_NAME]

        # Get collections
        db.execution_history = db.db["execution_history"]
        db.patterns = db.db["patterns"]
        db.optimization_suggestions = db.db["optimization_suggestions"]
        db.agent_scores = db.db["agent_scores"]
        db.workflows = db.db["workflows"]
        db.deployments = db.db["deployments"]

        logger.info("📊 Creating database indexes...")

        # Execution history indexes
        await db.execution_history.create_index([("agent_id", ASCENDING)])
        await db.execution_history.create_index([("timestamp", DESCENDING)])
        await db.execution_history.create_index([
            ("agent_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        logger.info("✅ execution_history indexes created")

        # Patterns indexes
        await db.patterns.create_index([("timestamp", DESCENDING)])
        logger.info("✅ patterns indexes created")

        # Optimization suggestions indexes
        await db.optimization_suggestions.create_index([("timestamp", DESCENDING)])
        await db.optimization_suggestions.create_index([("workflow", ASCENDING)])
        logger.info("✅ optimization_suggestions indexes created")

        # Agent scores indexes
        await db.agent_scores.create_index([("agent_id", ASCENDING)], unique=True)
        await db.agent_scores.create_index([("overall_score", DESCENDING)])
        logger.info("✅ agent_scores indexes created")

        # Workflows indexes
        await db.workflows.create_index([("workflow_id", ASCENDING)], unique=True)
        await db.workflows.create_index([("created_at", DESCENDING)])
        logger.info("✅ workflows indexes created")

        # Deployments indexes
        await db.deployments.create_index([("deployment_id", ASCENDING)], unique=True)
        await db.deployments.create_index([("created_at", DESCENDING)])
        logger.info("✅ deployments indexes created")

        logger.info("✅ MongoDB Connected Successfully!")
        logger.info(f"📁 Database: {MONGODB_DB_NAME}")
        logger.info(f"🔗 URL: {MONGODB_URL}")

        return True

    except Exception as e:
        logger.error(f"❌ MongoDB Connection Failed: {e}")
        return False


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("✅ MongoDB Connection Closed")


async def get_database():
    """Get database instance"""
    return db.db


# Utility functions

async def drop_all_collections():
    """Drop all collections (for testing)"""
    try:
        await db.execution_history.drop()
        await db.patterns.drop()
        await db.optimization_suggestions.drop()
        await db.agent_scores.drop()
        await db.workflows.drop()
        await db.deployments.drop()
        logger.info("✅ All collections dropped")
    except Exception as e:
        logger.error(f"❌ Error dropping collections: {e}")


async def get_stats():
    """Get database statistics"""
    try:
        execution_count = await db.execution_history.count_documents({})
        pattern_count = await db.patterns.count_documents({})
        optimization_count = await db.optimization_suggestions.count_documents({})
        agent_count = await db.agent_scores.count_documents({})
        workflow_count = await db.workflows.count_documents({})
        deployment_count = await db.deployments.count_documents({})

        return {
            "execution_history": execution_count,
            "patterns": pattern_count,
            "optimization_suggestions": optimization_count,
            "agent_scores": agent_count,
            "workflows": workflow_count,
            "deployments": deployment_count,
            "total": execution_count + pattern_count + optimization_count + agent_count + workflow_count + deployment_count
        }

    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return {}
