import json 
from datetime import datetime 
from typing import Dict, List, Any 
import asyncio 
from database import db 

class ExecutionTrackerMCP:
    """Tracks EVERY agent execution
    Records: time, memory, quality, success, cost"""

    def __init__(self): 
        self.execution = []

    async def track(self, agent_id: str, task: str, result: Dict[str, Any]) -> Dict: 
        """track execution data"""
        execution_data = {
            "_id": None,
            "agent_id": agent_id,
            "task": task,
            "execution_time": result.get("time", 0),
            "memory_used": result.get("memory", 0),
            "success": result.get("success", True),
            "quality_score": result.get("quality", 8.5),
            "cost": result.get("cost", 0.10),
            "input_size": result.get("input_size", 0),
            "output_size": result.get("output_size", 0),
            "output_quality": result.get("output_quality", 8.5),
            "timestamp": datetime.utcnow().isoformat(),
            "result_summary": result.get("summary", ""),
            "errors": result.get("errors", []),
            "metadata": result.get("metadata", {})
        }

        try: 
            collection = db.execution_history
            insert_result = await collection.insert_one(execution_data)
            execution_data['_id'] = str(insert_result.inserted_id)
            print(f"Tracked execution: {agent_id} - {task}")
        except Exception as e: 
            print(f"Tracking error {e}")

        return execution_data

    async def get_history(self, agent_id: str = None, limit: int = 100) -> List[Dict]:
        """Get execution history"""
        try: 
            collection = db.execution_history
            query = {"agent_id", agent_id} if agent_id else {}

            executions = await collections.find(query).sort(
                "timestamp", -1
            ).limit(limit).to_list(length=limit)

            return executions 
        except Exception as e: 
            print(f"Error fetching history: {e}")
            return []

    async def get_stats(self, agent_id: str = None) -> Dict: 
        """Get execution statistics"""

        history = await self.get_history(agent_id, limit=100)

        if not history:
            return {
                "total_execution": 0,
                "avg_time": 0,
                "avg_quality": 0,
                "success_rate": 0,
            }

        times = [e["execution_time"] for e in history if e["execution_time"]]
        qualities = [e["quality_score"] for e in history if e["quality_score"]]
        successes = [1 for e in history if e["success"]]

        return {
            "total_executions": len(history),
            "avg_time": sum(times) / len(times) if times else 0,
            "avg_quality": sum(qualities) / len(qualities) if qualities else 0,
            "success_rate": len(successes) / len(history) * 100 if history else 0,
            "fastest_execution": min(times) if times else 0,
            "slowest_execution": max(times) if times else 0,
            "best_quality": max(qualities) if qualities else 0
        }

execution_tracker = ExecutionTrackerMCP()