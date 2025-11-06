# Graphiti Advanced Tutorial: Building a Conversational AI Agent

This advanced tutorial demonstrates how to use Graphiti in a more complex, real-world application. We'll build a conversational sales agent for a shoe store using Graphiti for knowledge and the LangGraph library for agentic logic.

## What You'll Learn

-   **Data Ingestion**: How to load a product catalog into your knowledge graph.
-   **Personalization**: How to use Graphiti to remember user preferences and conversation history.
-   **Tool Use**: How to create a "tool" that allows your AI agent to search the knowledge graph.
-   **LangGraph Integration**: How to build a stateful, conversational agent that uses Graphiti as its long-term memory.

## Prerequisites

In addition to the requirements from the beginner tutorial, you'll also need:

-   **LangChain and LangGraph**: These libraries are used to build the conversational agent.
-   **A `manybirds_products.json` file**: This file is expected to be in the `examples/data` directory relative to the root of the repository.

## Setup Instructions

1.  **Install Additional Dependencies**:
    Open your terminal and run the following command to install the necessary libraries:
    ```bash
    pip install langchain-openai langgraph
    ```

2.  **Set Up Environment Variables**:
    As with the beginner tutorial, make sure your `OPENAI_API_KEY` and Neo4j connection details are set as environment variables or in a `.env` file.

3.  **Run the Tutorial**:
    Navigate to the `Code new/advanced` directory in your terminal and run the script:
    ```bash
    python tutorial.py
    ```

## Understanding the Code

The `tutorial.py` script is a command-line application that simulates a conversation with a sales agent. Here's a breakdown of the key concepts:

-   **SECTION 1: Configuration**: Sets up the environment and logging.
-   **SECTION 2: Data Ingestion and Setup**: Contains a function to clear the database, load a product catalog from a JSON file, and create a user profile in the graph. **Note:** This is a destructive operation and will wipe your graph.
-   **SECTION 3: Creating the LangGraph Agent**:
    -   **State**: Defines the structure of the agent's memory.
    -   **Tool (`get_shoe_data`)**: A function that the AI agent can "call" to search the Graphiti knowledge graph for product information.
    -   **Chatbot Node**: The core logic of the agent. It retrieves personalized context from Graphiti, constructs a prompt for the language model, and saves the conversation back to the graph.
-   **SECTION 4: Defining the Graph Structure**: Uses `StateGraph` from LangGraph to define the flow of the conversation. The agent can either respond directly or decide to use its `get_shoe_data` tool to find more information.
-   **SECTION 5: Running the Agent**: An interactive loop that allows you to chat with the agent from your command line.

This example showcases the power of combining a knowledge graph like Graphiti with an agent framework like LangGraph. The knowledge graph provides a persistent, queryable memory that makes the agent more knowledgeable and personalized over time.
