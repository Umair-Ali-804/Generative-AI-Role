"""
Streamlit frontend for the multi-agent system
"""
import streamlit as st
import requests
import time
import json
from datetime import datetime
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Multi-Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: bold;
        display: inline-block;
    }
    .status-pending {
        background-color: #ffd700;
        color: #000;
    }
    .status-running {
        background-color: #4169e1;
        color: #fff;
    }
    .status-completed {
        background-color: #32cd32;
        color: #fff;
    }
    .status-failed {
        background-color: #dc143c;
        color: #fff;
    }
    .agent-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border-left: 4px solid;
    }
    .agent-researcher {
        border-left-color: #4169e1;
        background-color: #e6f2ff;
    }
    .agent-analyst {
        border-left-color: #32cd32;
        background-color: #e6ffe6;
    }
    .agent-synthesizer {
        border-left-color: #ff8c00;
        background-color: #fff5e6;
    }
    .agent-supervisor {
        border-left-color: #9370db;
        background-color: #f3e6ff;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def create_task(task: str, context: dict):
    """Create a new task via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/tasks",
            json={"task": task, "context": context}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating task: {str(e)}")
        return None


def get_task_status(task_id: str):
    """Get task status via API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def get_task_result(task_id: str):
    """Get full task result via API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}/result")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def list_tasks(limit: int = 10, status: Optional[str] = None):
    """List all tasks via API"""
    try:
        params = {"limit": limit}
        if status:
            params["status"] = status
        response = requests.get(f"{API_BASE_URL}/api/tasks", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error listing tasks: {str(e)}")
        return None


def render_status_badge(status: str):
    """Render status badge with color"""
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{status.upper()}</span>'


def render_agent_message(agent: str, content: str):
    """Render agent message with styling"""
    agent_class = f"agent-{agent.lower()}"
    return f"""
    <div class="agent-message {agent_class}">
        <strong>🤖 {agent.title()}</strong><br/>
        {content}
    </div>
    """


# Initialize session state
if 'current_task_id' not in st.session_state:
    st.session_state.current_task_id = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # API Health Check
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
        st.warning("Make sure to run: `uvicorn api:app --reload`")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["New Task", "Task History", "Monitor Task"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Auto-refresh for monitoring
    if page == "Monitor Task" and st.session_state.current_task_id:
        st.session_state.auto_refresh = st.checkbox("Auto-refresh", value=True)
        if st.session_state.auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 1, 10, 2)


# Main content
st.markdown('<h1 class="main-header">🤖 Multi-Agent System</h1>', unsafe_allow_html=True)

if not api_healthy:
    st.error("⚠️ API is not running. Please start the FastAPI server first.")
    st.code("uvicorn api:app --reload --port 8000", language="bash")
    st.stop()

# Page: New Task
if page == "New Task":
    st.markdown("### 📝 Create New Task")
    
    with st.form("task_form"):
        task = st.text_area(
            "Task Description",
            placeholder="Enter your task here... e.g., Research AI trends and analyze their impact",
            height=150
        )
        
        col1, col2 = st.columns(2)
        with col1:
            industry = st.text_input("Industry (optional)", placeholder="e.g., technology")
        with col2:
            focus_areas = st.text_input("Focus Areas (optional)", placeholder="e.g., ML, AI, automation")
        
        submitted = st.form_submit_button("🚀 Submit Task", use_container_width=True)
    
    if submitted and task:
        context = {}
        if industry:
            context["industry"] = industry
        if focus_areas:
            context["focus_areas"] = [area.strip() for area in focus_areas.split(",")]
        
        with st.spinner("Creating task..."):
            result = create_task(task, context)
            
        if result:
            st.success(f"✅ Task created successfully!")
            st.session_state.current_task_id = result["task_id"]
            st.info(f"Task ID: `{result['task_id']}`")
            
            if st.button("📊 Monitor This Task"):
                st.session_state.current_task_id = result["task_id"]
                st.rerun()

# Page: Task History
elif page == "Task History":
    st.markdown("### 📜 Task History")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "pending", "running", "completed", "failed"]
        )
    with col2:
        limit = st.number_input("Show tasks", min_value=5, max_value=50, value=10)
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    status_filter = None if filter_status == "All" else filter_status
    tasks_data = list_tasks(limit=limit, status=status_filter)
    
    if tasks_data and tasks_data["tasks"]:
        st.markdown(f"**Total tasks: {tasks_data['total']}**")
        
        for task in tasks_data["tasks"]:
            with st.expander(
                f"{task['task'][:80]}... - {render_status_badge(task['status'])}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Task ID:** `{task['task_id']}`")
                    st.markdown(f"**Status:** {render_status_badge(task['status'])}", unsafe_allow_html=True)
                    st.markdown(f"**Created:** {task['created_at']}")
                    if task['completed_at']:
                        st.markdown(f"**Completed:** {task['completed_at']}")
                    st.markdown(f"**Iterations:** {task['iterations']}")
                
                with col2:
                    if st.button("View Details", key=f"view_{task['task_id']}"):
                        st.session_state.current_task_id = task['task_id']
                        st.rerun()
                
                if task['final_response']:
                    st.markdown("**Final Response:**")
                    st.info(task['final_response'])
                
                if task.get('error'):
                    st.error(f"**Error:** {task['error']}")
    else:
        st.info("No tasks found.")

# Page: Monitor Task
elif page == "Monitor Task":
    st.markdown("### 📊 Monitor Task")
    
    # Task ID input
    task_id_input = st.text_input(
        "Task ID",
        value=st.session_state.current_task_id or "",
        placeholder="Enter task ID to monitor"
    )
    
    if task_id_input:
        st.session_state.current_task_id = task_id_input
        
        # Get task status
        status_data = get_task_status(task_id_input)
        
        if status_data:
            # Display status
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", status_data['status'].upper())
            with col2:
                st.metric("Iterations", status_data['iterations'])
            with col3:
                st.metric("Current Agent", status_data['current_agent'] or "N/A")
            with col4:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Progress indicator
            if status_data['status'] == 'running':
                st.progress(0.5, "Task is running...")
            elif status_data['status'] == 'completed':
                st.progress(1.0, "Task completed!")
            elif status_data['status'] == 'failed':
                st.error("Task failed!")
            
            # Get full results if completed
            if status_data['status'] in ['completed', 'failed']:
                result_data = get_task_result(task_id_input)
                
                if result_data:
                    # Display final response
                    st.markdown("### 🎯 Final Response")
                    if result_data.get('final_response'):
                        st.success(result_data['final_response'])
                    else:
                        st.warning("No final response available")
                    
                    # Display conversation history
                    st.markdown("### 💬 Conversation History")
                    if result_data.get('messages'):
                        for i, msg in enumerate(result_data['messages']):
                            msg_type = msg.get('type', 'Unknown')
                            content = msg.get('content', '')
                            
                            # Determine agent from message type
                            if 'System' in msg_type:
                                continue  # Skip system messages
                            elif 'Human' in msg_type:
                                st.markdown(f"**👤 User:** {content}")
                            elif 'AI' in msg_type:
                                st.markdown(f"**🤖 Assistant:** {content}")
                            else:
                                st.markdown(f"**{msg_type}:** {content}")
                    
                    # Display metadata
                    with st.expander("🔍 Metadata"):
                        st.json(result_data.get('metadata', {}))
            
            # Auto-refresh
            if st.session_state.auto_refresh and status_data['status'] == 'running':
                time.sleep(refresh_interval)
                st.rerun()
        else:
            st.error("Task not found or error retrieving task status.")
    else:
        st.info("Enter a task ID to monitor its progress.")


# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Multi-Agent System v1.0.0 | "
    "Built with LangGraph, FastAPI & Streamlit</div>",
    unsafe_allow_html=True
)