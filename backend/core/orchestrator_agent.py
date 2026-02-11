from typing import List, Dict, Any
from datetime import datetime

from config.archestra_config import archestra_gateway
from mcps.execution_tracker_mcp import execution_tracker
from mcps.pattern_learner_mcp import pattern_learner
from mcps.optimizer_mcp import optimizer
from mcps.quality_validator_mcp import quality_validator
from mcps.agent_scorer_mcp import agent_scorer


class OrchestratorAgent:
    def __init__(self):
        self.execution_count = 0
        self.optimization_count = 0

    # async def register_with_archestra(self):
    #     """
    #     Notify Archestra about our MCPs using JSON-RPC
    #     """
    #     print("\n🔗 Notifying Archestra about our MCPs...")

    #     mcp_info = {
    #         "system": "Self-Learning Agent System",
    #         "status": "ready",
    #         "version": "1.0.0",
    #         "mcps": [
    #             "ExecutionTracker",
    #             "PatternLearner",
    #             "Optimizer",
    #             "QualityValidator",
    #             "AgentScorer"
    #         ],
    #         "capabilities": [
    #             "Self-learning",
    #             "Pattern recognition",
    #             "Optimization suggestions",
    #             "Quality validation",
    #             "Agent scoring"
    #         ]
    #     }

    #     # Send info through MCP Gateway using JSON-RPC
    #     result = await archestra_gateway.send_to_mcp_gateway(mcp_info)

    #     if result and "error" not in result:
    #         print("✅ Notified Archestra - System ready!")
    #         return result
    #     else:
    #         print("⚠️ Archestra notification sent (may be async)")
    #         return result


    async def execute(self, user_task: str, available_agents: List[str]) -> Dict[str, Any]:
        """
        Execute workflow with optimization using Archestra Gateways
        """

        print(f"\n🚀 ORCHESTRATOR: Starting task - {user_task}")

        # Check if Archestra is online
        archestra_online = await archestra_gateway.check_archestra_health()

        # Step 1: Get execution history
        print("📊 Step 1: Fetching execution history...")
        execution_history = await execution_tracker.get_history(limit=100)
        print(f"   Found {len(execution_history)} previous executions")

        # Step 2: Learn patterns
        print("🧠 Step 2: Learning patterns...")
        patterns = await pattern_learner.learn(execution_history)

        # If Archestra is online, use LLM for insights
        llm_insight = None
        if archestra_online:
            print("   📡 Getting LLM insights from Llama3.2 via Archestra...")

            llm_prompt = f"""
            Analyze these execution patterns and suggest ONE key optimization:

            Task: {user_task}
            Total executions: {len(execution_history)}
            Agents: {', '.join(available_agents)}

            Based on patterns, what's the best optimization?
            Answer in 1-2 sentences.
            """

            llm_insight = await archestra_gateway.send_to_llm_proxy(llm_prompt)

            if llm_insight:
                print(f"   🤖 LLM: {llm_insight[:150]}...")
            else:
                print("   ⚠️ LLM insight failed")

        print("   Learned from execution data")

        # Step 3: Get optimization suggestions
        print("⚡ Step 3: Generating optimizations...")
        suggestions = await optimizer.suggest_optimization(
            workflow=available_agents,
            execution_history=execution_history,
            goal="balanced"
        )

        if suggestions:
            print(f"   Found {len(suggestions)} optimization opportunities")
            best_suggestion = suggestions[0]
            print(f"   Best: {best_suggestion['type']} - {best_suggestion['improvement']}")
        else:
            best_suggestion = None
            print("   No optimizations found")

        # Step 4: Score agents
        print("⭐ Step 4: Scoring agents...")
        agent_scores = {}

        for agent_id in available_agents:
            agent_executions = [e for e in execution_history if e.get("agent_id") == agent_id]
            score = await agent_scorer.score_agent(agent_id, agent_executions)
            agent_scores[agent_id] = score
            print(f"   {agent_id}: Score {score['overall_score']}/10")

        # Step 5: Select optimized workflow
        print("🔄 Step 5: Selecting optimized workflow...")
        if best_suggestion and best_suggestion.get("confidence", 0) > 0.7:
            optimized_workflow = best_suggestion["to"]
            optimization_applied = best_suggestion["type"]
            print(f"   Applying: {optimization_applied}")
            self.optimization_count += 1
        else:
            optimized_workflow = available_agents
            optimization_applied = None
            print("   Using standard workflow order")

        # Step 6: Send workflow payload to Archestra A2A
        print("▶️ Step 6: Preparing workflow for Archestra...")

        workflow_payload = {
            "type": "workflow_execution",
            "task": user_task,
            "workflow": optimized_workflow if isinstance(optimized_workflow, list) else [optimized_workflow],
            "optimization": optimization_applied,
            "agents": agent_scores,
            "patterns": patterns,
            "llm_insight": llm_insight,
            "timestamp": datetime.utcnow().isoformat()
        }

        if archestra_online:
            try:
                print("   📡 Sending to Archestra A2A Gateway...")
                await archestra_gateway.send_to_a2a_gateway(workflow_payload)
                print("   ✅ Archestra received workflow")
            except Exception as e:
                print(f"   ⚠️ Failed to send workflow to Archestra A2A: {e}")

        # Step 7: Execute locally (simulate)
        print("💾 Step 7: Executing workflow locally...")

        results = {
            "task": user_task,
            "workflow": optimized_workflow,
            "agents_results": [],
            "success": True,
            "archestra_integrated": archestra_online
        }

        for agent_id in (optimized_workflow if isinstance(optimized_workflow, list) else [optimized_workflow]):
            agent_result = {
                "agent_id": agent_id,
                "status": "completed",
                "time": 2.5,
                "quality": 9.2,
                "data": {"processed": True}
            }

            results["agents_results"].append(agent_result)

            await execution_tracker.track(agent_id, user_task, {
                "time": agent_result["time"],
                "quality": agent_result["quality"],
                "success": True,
                "summary": f"Executed {agent_id} for {user_task}"
            })

        # Step 8: Validate quality
        print("✅ Step 8: Validating output quality...")
        validation = await quality_validator.validate(results)
        results["validation"] = validation
        print(f"   Quality Score: {validation['overall_quality']}/1.0")

        # Step 9: Track final execution
        print("📊 Step 9: Recording execution...")
        total_time = sum(r["time"] for r in results["agents_results"])

        await execution_tracker.track("Orchestrator", user_task, {
            "time": total_time,
            "quality": validation["overall_quality"],
            "success": True,
            "cost": total_time * 0.05,
            "summary": f"Orchestrated workflow - {optimization_applied or 'standard'}"
        })

        self.execution_count += 1

        print("✅ Workflow complete!\n")

        return {
            "status": "success",
            "task": user_task,
            "workflow": optimized_workflow,
            "optimization_applied": optimization_applied,
            "llm_insight": llm_insight,
            "results": results,
            "execution_stats": {
                "total_executions": self.execution_count,
                "optimizations_applied": self.optimization_count,
                "agents_used": len(results["agents_results"]),
                "total_time": total_time,
                "quality_score": validation["overall_quality"]
            }
        }


# IMPORTANT: create global instance for import
orchestrator_agent = OrchestratorAgent()
