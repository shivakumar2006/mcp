from typing import Dict, List, Any
from database import db
import statistics

class AgentScorerMCP:
    """
    Rates agents based on execution history
    Scores: speed, accuracy, reliability, cost
    """
    
    async def score_agent(self, agent_id: str, executions: List[Dict] = None) -> Dict[str, Any]:
        """
        Score an agent based on performance
        """
        
        if executions is None:
            # Get from database
            try:
                collection = db.execution_history
                executions = await collection.find(
                    {"agent_id": agent_id}
                ).limit(100).to_list(length=100)
            except:
                executions = []
        
        if not executions:
            return {
                "agent_id": agent_id,
                "score": 0,
                "message": "No execution history"
            }
        
        # Extract metrics
        times = [e.get("execution_time", 0) for e in executions if e.get("execution_time")]
        qualities = [e.get("quality_score", 8) for e in executions if e.get("quality_score")]
        successes = [1 for e in executions if e.get("success")]
        costs = [e.get("cost", 0.1) for e in executions if e.get("cost")]
        
        # Calculate scores
        avg_time = statistics.mean(times) if times else 10
        avg_quality = statistics.mean(qualities) if qualities else 8
        success_rate = (len(successes) / len(executions) * 100) if executions else 0
        avg_cost = statistics.mean(costs) if costs else 0.1
        
        # Normalize scores (0-10)
        speed_score = max(0, 10 - (avg_time / 10))  # Faster = higher
        accuracy_score = (avg_quality / 10) * 10     # Quality normalized
        reliability_score = success_rate / 10         # Success rate normalized
        cost_score = max(0, 10 - (avg_cost * 100))  # Lower cost = higher
        
        # Overall score
        overall_score = (
            speed_score * 0.25 +
            accuracy_score * 0.35 +
            reliability_score * 0.25 +
            cost_score * 0.15
        )
        
        # Determine rank
        if overall_score >= 9:
            rank = "🌟 Top Agent"
        elif overall_score >= 8:
            rank = "⭐ Excellent"
        elif overall_score >= 7:
            rank = "✅ Good"
        elif overall_score >= 6:
            rank = "⚠️ Fair"
        else:
            rank = "❌ Poor"
        
        return {
            "agent_id": agent_id,
            "speed_score": round(speed_score, 2),
            "accuracy_score": round(accuracy_score, 2),
            "reliability_score": round(reliability_score, 2),
            "cost_score": round(cost_score, 2),
            "overall_score": round(overall_score, 2),
            "rank": rank,
            "metrics": {
                "avg_time": round(avg_time, 2),
                "avg_quality": round(avg_quality, 2),
                "success_rate": round(success_rate, 1),
                "avg_cost": round(avg_cost, 4),
                "total_executions": len(executions)
            },
            "recommendation": "Recommended for production" if overall_score >= 8 else "Use with caution" if overall_score >= 6 else "Needs improvement"
        }
    
    async def score_all_agents(self) -> List[Dict]:
        """
        Score all agents and rank them
        """
        try:
            collection = db.execution_history
            agents = await collection.distinct("agent_id")
            
            scores = []
            for agent_id in agents:
                score = await self.score_agent(agent_id)
                scores.append(score)
            
            # Sort by overall score
            scores.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
            
            return scores
        except:
            return []

# Create global instance
agent_scorer = AgentScorerMCP()