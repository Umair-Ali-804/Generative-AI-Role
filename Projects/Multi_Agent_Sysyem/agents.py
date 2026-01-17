"""
Agent definitions for the multi-agent system
"""
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from state import AgentState
from config import llm, llm_2
from prompts import research_agent_prompt, analysis_agent_prompt, synthesis_agent_prompt, supervisor_agent_prompt


class ResearchAgent:
    """Agent responsible for research and information gathering"""
    
    def __init__(self):
        self.llm = llm
        self.name = "researcher"
        
    def __call__(self, state: AgentState) -> AgentState:
        messages = [
            SystemMessage(content=research_agent_prompt),
            *state["messages"]
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            **state,
            "messages": [response],
            "current_agent": self.name,
            "iterations": state.get("iterations", 0) + 1
        }


class AnalysisAgent:
    """Agent responsible for analyzing research and data"""
    
    def __init__(self):
        self.llm = llm_2
        self.name = "analyst"
        
    def __call__(self, state: AgentState) -> AgentState:
        
        messages = [
            SystemMessage(content=analysis_agent_prompt),
            *state["messages"]
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            **state,
            "messages": [response],
            "current_agent": self.name,
            "iterations": state.get("iterations", 0) + 1
        }


class SynthesisAgent:
    """Agent responsible for synthesizing information and creating final output"""
    
    def __init__(self):
        self.llm = llm
        self.name = "synthesizer"
        
    def __call__(self, state: AgentState) -> AgentState: 
        messages = [
            SystemMessage(content=synthesis_agent_prompt),
            *state["messages"]
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            **state,
            "messages": [response],
            "current_agent": self.name,
            "final_response": response.content,
            "iterations": state.get("iterations", 0) + 1
        }


class SupervisorAgent:
    """Agent that coordinates other agents and routes tasks"""
    
    def __init__(self):
        self.llm = llm_2
        self.name = "supervisor"
        
    def __call__(self, state: AgentState) -> AgentState:
        
        messages = [
            SystemMessage(content=supervisor_agent_prompt),
            *state["messages"],
            HumanMessage(content=f"Current task: {state.get('task', '')}")
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            **state,
            "messages": [response],
            "current_agent": self.name,
            "metadata": {
                **state.get("metadata", {}),
                "supervisor_decision": response.content
            }
        }