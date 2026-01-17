"""
Main execution file for the multi-agent system
"""

from langchain_core.messages import HumanMessage
from graph import graph
from state import AgentState
from config import RECURSION_LIMIT


def run_agent_system(task: str, context: dict = None) -> dict:
    """
    Run the multi-agent system with a given task

    Args:
        task: The task description
        context: Additional context for the agents

    Returns:
        Final state with results
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=task)],
        "current_agent": "",
        "task": task,
        "context": context or {},
        "iterations": 0,
        "final_response": None,
        "metadata": {}
    }

    # Run the graph
    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": RECURSION_LIMIT}
    )

    return final_state


def main():
    """Example usage of the multi-agent system"""

    while True:
        task = input("Type here (or 'quit' to exit): ").strip()

        if task.lower() in ["quit", "exit", "bye"]:
            print("Exiting multi-agent system.")
            break

        context = {
            "industry": "technology",
            "focus_areas": [
                "machine learning",
                "automation",
                "AI ethics",
                "deep learning"
            ]
        }

        print("Starting multi-agent system...")
        print(f"Task: {task}\n")

        result = run_agent_system(task, context)

        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"\nIterations: {result['iterations']}")
        print(f"Final Agent: {result['current_agent']}")
        print(f"\nFinal Response:\n{result.get('final_response', 'No final response')}")
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
