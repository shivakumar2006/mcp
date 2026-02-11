from typing import Dict, List, Any
from database import db

class OptimizerMCP:
    """
    Suggests workflow optimizations
    Reorders agents for speed/quality
    """
    
    async def suggest_optimization(self, 
                                   workflow: List[str],
                                   execution_history: List[Dict],
                                   goal: str = "speed") -> List[Dict]:
        """
        Suggest optimizations for workflow
        goal: "speed", "quality", or "balanced"
        """
        
        if not execution_history or len(execution_history) < 3:
            return []
        
        suggestions = []
        
        # Get agent performance data
        agent_stats = {}
        for exec_data in execution_history:
            agent_id = exec_data.get("agent_id")
            if agent_id not in agent_stats:
                agent_stats[agent_id] = []
            
            agent_stats[agent_id].append({
                "time": exec_data.get("execution_time", 1),
                "quality": exec_data.get("quality_score", 8),
                "success": exec_data.get("success", True)
            })
        
        # Suggestion 1: Reorder by speed
        if goal in ["speed", "balanced"]:
            agent_times = {}
            for agent_id, stats in agent_stats.items():
                agent_times[agent_id] = sum(s["time"] for s in stats) / len(stats)
            
            # Sort workflow by agent speed
            sorted_workflow = sorted(
                workflow,
                key=lambda a: agent_times.get(a, 999)
            )
            
            if sorted_workflow != workflow:
                current_time = sum(agent_times.get(a, 1) for a in workflow)
                new_time = sum(agent_times.get(a, 1) for a in sorted_workflow)
                speedup = ((current_time - new_time) / current_time * 100) if current_time > 0 else 0
                
                suggestions.append({
                    "type": "reorder",
                    "from": workflow,
                    "to": sorted_workflow,
                    "improvement": f"{speedup:.1f}% faster",
                    "confidence": 0.85 if len(execution_history) > 10 else 0.65,
                    "reason": "Fastest agents run first to fail fast"
                })
        
        # Suggestion 2: Parallel execution
        if len(workflow) > 2:
            # Some agents might run in parallel
            parallel_suggestion = {
                "type": "parallel",
                "from": workflow,
                "to": f"({workflow[0]} || {workflow[1]}) → {workflow[2:]}" if len(workflow) > 2 else None,
                "improvement": "30-50% faster",
                "confidence": 0.72,
                "reason": "Independent agents can run in parallel"
            }
            
            if parallel_suggestion["to"]:
                suggestions.append(parallel_suggestion)
        
        # Suggestion 3: Agent replacement
        best_agent = max(
            agent_stats.items(),
            key=lambda x: sum(s["quality"] for s in x[1]) / len(x[1])
        )[0]
        
        for agent in workflow:
            if agent != best_agent:
                suggestions.append({
                    "type": "replace",
                    "from": agent,
                    "to": best_agent,
                    "improvement": "Better quality",
                    "confidence": 0.70,
                    "reason": f"{best_agent} has better track record"
                })
                break
        
        # Save suggestions
        try:
            await db.optimization_suggestions.insert_one({
                "workflow": workflow,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass
        
        return sorted(
            suggestions,
            key=lambda x: x.get("confidence", 0),
            reverse=True
        )

# Create global instance
optimizer = OptimizerMCP()