"""
LangGraph workflow definition
"""
from langgraph.graph import StateGraph, END
from state import AgentState
from agents import ResearchAgent, AnalysisAgent, SynthesisAgent, SupervisorAgent
from config import MAX_ITERATIONS, RECURSION_LIMIT


def create_graph():
    """Create and configure the multi-agent graph"""
    
    # Initialize agents
    researcher = ResearchAgent()
    analyst = AnalysisAgent()
    synthesizer = SynthesisAgent()
    supervisor = SupervisorAgent()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("researcher", researcher)
    workflow.add_node("analyst", analyst)
    workflow.add_node("synthesizer", synthesizer)
    
    # Define routing logic
    def route_supervisor(state: AgentState) -> str:
        """Route based on supervisor's decision"""
        if state.get("iterations", 0) >= MAX_ITERATIONS:
            return "synthesizer"
        
        decision = state.get("metadata", {}).get("supervisor_decision", "")
        decision_lower = decision.lower().strip()
        
        if "finish" in decision_lower or state.get("final_response"):
            return END
        elif "research" in decision_lower:
            return "researcher"
        elif "analy" in decision_lower:
            return "analyst"
        elif "synth" in decision_lower:
            return "synthesizer"
        else:
            return "researcher"  # Default
    
    def route_to_supervisor(state: AgentState) -> str:
        """Route back to supervisor after agent execution"""
        if state.get("final_response"):
            return END
        return "supervisor"
    
    # Add edges
    workflow.set_entry_point("supervisor")
    
    # Supervisor routes to agents
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "researcher": "researcher",
            "analyst": "analyst",
            "synthesizer": "synthesizer",
            END: END
        }
    )
    
    # Agents route back to supervisor
    workflow.add_conditional_edges("researcher", route_to_supervisor)
    workflow.add_conditional_edges("analyst", route_to_supervisor)
    workflow.add_edge("synthesizer", END)
    
    # Compile graph
    app = workflow.compile()
    
    return app


# Create the compiled graph
graph = create_graph()