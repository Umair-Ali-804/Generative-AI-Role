"""
FastAPI backend for the multi-agent system
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
import uuid
import asyncio
from collections import defaultdict

from graph import graph
from state import AgentState
from langchain_core.messages import HumanMessage
from config import RECURSION_LIMIT

app = FastAPI(
    title="Multi-Agent System API",
    description="API for LangGraph multi-agent system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for tasks
tasks_storage = {}
results_storage = {}


class TaskRequest(BaseModel):
    """Request model for creating a new task"""
    task: str = Field(..., description="Task description")
    context: Optional[Dict] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Research AI trends and analyze their impact",
                "context": {"industry": "technology"}
            }
        }


class TaskResponse(BaseModel):
    """Response model for task creation"""
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    """Model for task status"""
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    iterations: int
    current_agent: str
    final_response: Optional[str]
    error: Optional[str]


class AgentMessage(BaseModel):
    """Model for agent messages"""
    agent: str
    content: str
    timestamp: str


async def run_agent_task(task_id: str, task: str, context: dict):
    """
    Run the agent system asynchronously
    """
    try:
        tasks_storage[task_id]["status"] = "running"
        
        initial_state: AgentState = {
            "messages": [HumanMessage(content=task)],
            "current_agent": "",
            "task": task,
            "context": context,
            "iterations": 0,
            "final_response": None,
            "metadata": {}
        }
        
        # Run the graph
        final_state = await asyncio.to_thread(
            graph.invoke,
            initial_state,
            config={"recursion_limit": RECURSION_LIMIT}
        )
        
        # Store results
        results_storage[task_id] = final_state
        tasks_storage[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "iterations": final_state.get("iterations", 0),
            "current_agent": final_state.get("current_agent", ""),
            "final_response": final_state.get("final_response")
        })
        
    except Exception as e:
        tasks_storage[task_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent System API",
        "version": "1.0.0",
        "endpoints": {
            "create_task": "/api/tasks",
            "get_status": "/api/tasks/{task_id}",
            "get_result": "/api/tasks/{task_id}/result",
            "list_tasks": "/api/tasks"
        }
    }


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Create a new task for the multi-agent system
    """
    task_id = str(uuid.uuid4())
    
    tasks_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "task": request.task,
        "context": request.context,
        "iterations": 0,
        "current_agent": "",
        "final_response": None,
        "error": None
    }
    
    # Run task in background
    background_tasks.add_task(
        run_agent_task,
        task_id,
        request.task,
        request.context
    )
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Task created successfully"
    )


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a task
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    return TaskStatus(**task)


@app.get("/api/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """
    Get the full result of a completed task
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    
    if task["status"] == "pending" or task["status"] == "running":
        raise HTTPException(
            status_code=400,
            detail=f"Task is still {task['status']}"
        )
    
    if task["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Task failed: {task.get('error', 'Unknown error')}"
        )
    
    result = results_storage.get(task_id, {})
    
    # Extract messages for history
    messages = []
    for msg in result.get("messages", []):
        messages.append({
            "type": msg.__class__.__name__,
            "content": msg.content if hasattr(msg, 'content') else str(msg)
        })
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "task": task["task"],
        "context": task["context"],
        "iterations": task["iterations"],
        "final_response": task["final_response"],
        "messages": messages,
        "metadata": result.get("metadata", {})
    }


@app.get("/api/tasks")
async def list_tasks(limit: int = 10, status: Optional[str] = None):
    """
    List all tasks with optional filtering
    """
    tasks = list(tasks_storage.values())
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    # Sort by created_at descending
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task and its results
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks_storage[task_id]
    if task_id in results_storage:
        del results_storage[task_id]
    
    return {"message": "Task deleted successfully"}


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks_storage.values() if t["status"] == "running"]),
        "total_tasks": len(tasks_storage)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)