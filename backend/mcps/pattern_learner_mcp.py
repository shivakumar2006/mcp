from typing import Dict, List, Any 
from datetime import datetime 
import statistics 
from database import db 

class PatternLearnedMCP():
    """
    Learns patterns from execution data
    Finds: best agents, optimal orders, best combinations
    """

    async def learn(self, execution_history: List[Dict]) -> Dict[str, Any]:
        """Analyze execute history and find pattern"""
        if not execution_history or len(execution_history) < 3: 
            return {"message": "need at least 3 execution to learn"}

        patterns = {}

        # pattern1  best agents for tasks 
        agent_performance = {}
        for exec_data in execution_history:
            agent_id = exec_data.get("agent_id")
            quality = exec_data.get("quality_score", 0)
            time = exec_data.get("execution_time", 0)

            if agent_id not in agent_performance: 
                agent_performance[agent_id] = []

            agent_performance[agent_id].append({
                "quality": quality,
                "time": time,
                "success": exec_data.get("success", False)
            })

        agent_scores = {}
        for agent_id, performance in agent_performance.items():
            avg_quality = statistics.mean([p["quality"] for p in performances])
            avg_time = statistics.mean([p["time"] for p in performances])
            success_rate = sum(1 for p in performance if p["success"]) / len(performance * 100)

            agent_scores[agent_id] = {
                "avg_quality": round(avg_quality, 2),
                "avg_time": round(avg_time, 2),
                "success_rate": round(success_rate, 1),
                "score": round((avg_quality * 0.5 + (100 - avg_time) * 0.3 + success_rate * 0.2) / 100, 2)
            }
        
        patterns["agent_performance"] = agent_scores

        # pattern 2 quality vs speed tradeoff
        avg_quality = statistics.mean([e.get("quality_score", 0) for e in execution_history])
        avg_time = statistics.mean([e.get("execution_time", 0) for e in execution_history])

        patterns["quality_speed_tradeoff"] = {
            "avg_quality": round(avg_quality, 2),
            "avg_time": round(avg_time, 2),
            "recommendation": "Speed priority" if avg_time > 5 else "Quality priority",
            "fast_agents": [aid for aid, score in agent_scores.items() if score["avg_time"] < avg_time],
            "quality_agents": [aid for aid, score in agent_scores.items() if score["avg_quality"] > avg_quality]
        }

        # pattern 3 succes factor
        successfull = [e for e in execution_history if e.get("success")]
        failed = [e for e in execution_history if not e.get("success")]

        if successfull and failed: 
            patterns["success_factors"] = {
                "successful_avg_time": round(statistics.mean([e["execution_time"] for e in successful]), 2),
                "failed_avg_time": round(statistics.mean([e["execution_time"] for e in failed]), 2),
                "insight": "Slower executions more likely to fail" if patterns["success_factors"]["failed_avg_time"] > patterns["success_factors"]["successful_avg_time"] else "Speed doesn't guarantee success"
            }

        # save patterns 
        try: 
            await db.patterns.insert_one({
                "timestamp": datetime.utcnow().isoformat(),
                "patterns": patterns,
                "execution_count": len(execution_history)
            })
        except: 
            pass 

        return patterns

pattern_learner = PatternLearnedMCP()
        
