from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated, List, Optional

class AgentState(TypedDict):
    '''
    State shared across all agents in graph 
    '''
    messages:Annotated[List[BaseMessage],add_messages]
    current_agent:str
    task:str
    context:dict
    iterations:int
    final_response:Optional[str]
    metadata:dict