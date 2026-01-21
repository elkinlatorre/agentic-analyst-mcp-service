# test_agent.py (Updated with Token Monitoring)
import os
from dotenv import load_dotenv

# 1. Load environment variables before importing any app modules
load_dotenv()

from app.core.graph import app_graph
from langchain_core.messages import HumanMessage


def run_test():
    # Initial state
    inputs = {
        "messages": [
            HumanMessage(content="Search for today's weather in London and save it in a file named london.txt")
        ],
        "total_tokens": 0
    }

    print("--- Starting Agent Execution ---")

    # Run the graph
    for output in app_graph.stream(inputs):
        for node_name, node_state in output.items():
            print(f"\n" + "=" * 30)
            print(f"NODE EXECUTED: {node_name}")

            # Monitoring Tokens
            # In LangGraph, the 'output' contains the update from the node
            current_tokens = node_state.get("total_tokens", "N/A (Tool Node)")
            print(f"Cumulative Tokens so far: {current_tokens}")

            if "messages" in node_state:
                last_msg = node_state["messages"][-1]
                # Check if it's a Tool Call or final response
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    print(f"Action: Agent requested {len(last_msg.tool_calls)} tool(s).")
                else:
                    print(f"Content: {last_msg.content[:500]}...")
            print("=" * 30)


if __name__ == "__main__":
    run_test()