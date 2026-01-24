# The Autonomous Market Analyst

## Overview
This project demonstrates an advanced agentic AI use case: **"The Autonomous Market Analyst"**. It is a robust portfolio piece designed to showcase the orchestration of multiple MCP (Model Context Protocol) servers and local tools to perform end-to-end market research, data extraction, and reporting.

Unlike simple search bots, this agent acts as a diligent analyst. It autonomously:
1.  Identifies relevant data sources.
2.  "Cleans" and scrapes granular pricing data from specific URLs (overcoming snippet limitations).
3.  Persists data for comparison.
4.  Generates a final report upon human approval.

## Key Features
-   **Deep Web Scraping (MCP Fetch)**: Instead of relying on search engine snippets, the agent visits URLs, cleans the HTML, and extracts pure text for high-fidelity analysis.
-   **Structured Persistence (MCP SQLite)**: Extracted data (e.g., product prices, stock) is stored in a local SQLite database, enabling historical tracking and comparison.
-   **Human-in-the-Loop (HITL)**: Critical actions—specifically writing the final report to the local file system (saved in the `output/` directory)—require explicit human approval via API.
-   **Streaming Architecture**: The agent interaction is fully streaming, providing real-time feedback on its thought process and actions.

## Architecture

The system follows a modular architecture orchestrated by a central Long-Chain Graph agent.

```mermaid
flowchart TD
    User((User)) <--> API[FastAPI Server]
    
    subgraph "Agent Core"
        API <--> Orchestrator[LangGraph Agent]
        Orchestrator -- "Search" --> Tavily[Tavily Search Tool]
        Orchestrator -- "Persist State" --> Checkpointer[(checkpoints.db)]
    end

    subgraph "MCP Layer"
        Orchestrator -- "Scrape URL" --> ServerFetch[MCP Server Fetch]
        Orchestrator -- "Store Data" --> ServerSQLite[MCP Server SQLite]
    end

    subgraph "Persistence"
        ServerSQLite <--> DB[(external_data.db)]
    end

    subgraph "Local System"
        Orchestrator -- "Write Report" --> FileTool[File Output Tool]
        FileTool -.-> |"Requires Approval"| HumanCheck{Human Validation}
        HumanCheck -->|Approved| Disk[Local File System (output/)]
    end
```

### Workflow Description
0.  **State Management**: The agent's memory and state are persisted in an internal SQLite database (`checkpoints.db`). This allows the system to pause execution (waiting for human input) and resume exactly where it left off using the `thread_id`.
1.  **Search**: The agent uses **Tavily** to find relevant pages (e.g., "Nvidia RTX 5090 prices").
2.  **Fetch & Clean**: It uses the **MCP Fetch** server to navigate to specific retailer URLs found in step 1 and extract the full page content.
3.  **Store**: Validated data is sent to the **MCP SQLite** server and stored in the `external_data.db`.
4.  **Report**: The agent prepares a markdown summary. Before writing to disk, it pauses for **Human Validation**.
5.  **Approval**: The user approves the action via the `/chat/approve` endpoint, allowing the agent to finalize the file write.

## Project Structure
```text
AgenticAnalyst/
├── app/
│   ├── api/            # API Routes (Stream & Approval)
│   ├── core/           # Graph orchestration logic
│   ├── schemas/        # Pydantic models for Requests/Responses
│   ├── service/        # Business logic for Agent interaction
│   └── tools/          # Custom local tool definitions
├── external_data.db    # SQLite database for the MCP server
├── script_setup_mcp_sqlite.py # Setup script for the DB
├── main.py             # Entry point for the FastAPI server
├── requirements.txt    # Project dependencies
└── README.md           # This documentation
```

## Technologies Used
-   **Orchestration**: LangChain, LangGraph
-   **API Framework**: FastAPI, Uvicorn (Events Streaming)
-   **Protocols**: Model Context Protocol (MCP)
-   **Database**: SQLite, aiosqlite
-   **Validation**: Pydantic v2
-   **Search**: Tavily API

## Prerequisites & Setup

1.  **Python 3.12+** and **uv** (recommended) or pip.
2.  **MCP Servers**: Ensure `mcp-server-fetch` and `mcp-server-sqlite` are installed in your environment.

### Installation

1.  Clone the repository and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize the Database**: 
    **CRITICAL STEP**: You must run the setup script to prepare the database schema for the MCP server.
    ```bash
    python script_setup_mcp_sqlite.py
    ```
    *This creates/resets `external_data.db`.*

3.  **Configuration**:
    Create a `.env` file in the root directory. You will need API keys for Groq (LLM) and Tavily (Search).
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    TAVILY_API_KEY=your_tavily_api_key_here
    ```

## Usage

1.  **Start the Server**:
    Launch the FastAPI application.
    ```bash
    python -m app.main
    ```
    The server works on `http://localhost:8000`.

2.  **API Interaction**:
    The agent exposes two primary endpoints.

    ### 1. streaming Chat (`POST /api/v1/chat/stream`)
    Initiates the agent. The connection remains open (Server-Sent Events) to stream the agent's "thoughts" and tool calls.
    
    **Example Payload**:
    ```json
    {
      "message": "Busca en Tavily el precio de la Nvidia RTX 5090, usa fetch para leer el primer artículo que encuentres, guarda el precio en nuestra base de datos de SQLite y escribe un archivo con el producto y el precio"
    }
    ```
    
    **Behavior**:
    -   **Thread ID**: The `thread_id` field is **optional**. If omitted, the system generates a UUID automatically (e.g., `550e8400...`).
    -   **State persistence**: This ID uniquely identifies the session in the internal `checkpoints.db`. This database usage is crucial for the **Human-in-the-Loop** mechanism, allowing the server to retrieve the frozen state of the agent when the approval comes in.
    -   **Execution**: The agent will perform the search, fetch, and database operations autonomously.
    -   **Pause**: When it calls the file tool to write to `output/`, it pauses and returns a `waiting_approval` status with the `thread_id`.

    ### 2. Approval (`POST /api/v1/chat/approve`)
    Required to unblock the agent when it attempts sensitive actions (like file generation).
    
    **Example Payload**:
    ```json
    {
      "thread_id": "session_123",
      "approve": true
    }
    ```
    -   **`approve: true`**: The agent executes the file write and finishes the task.
    -   **`approve: false`**: The action is aborted.

    > **Note**: The "Report" generated is a simple text/markdown file saved locally containing the synthesized results of the market analysis.
