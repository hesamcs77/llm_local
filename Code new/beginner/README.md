# Graphiti Beginner Tutorial: Getting Started with Knowledge Graphs

Welcome to the beginner's guide to Graphiti! This tutorial will introduce you to the core concepts of Graphiti and walk you through the process of building and querying a simple knowledge graph.

## What You'll Learn

- **Connecting to a Database**: How to connect Graphiti to a Neo4j graph database.
- **Adding Data (Episodes)**: How to add your own data to the knowledge graph.
- **Basic and Advanced Search**: How to ask questions and get answers from your graph.
- **Node and Edge Search**: How to search for specific entities (nodes) and their relationships (edges).

## Prerequisites

To follow this tutorial, you'll need:

- **Python 3.9 or higher**
- An **OpenAI API key** (Graphiti uses OpenAI's language models to understand your data)
- **Neo4j Desktop**: A free tool for working with Neo4j databases. Make sure you have it installed and a local database is running.

## Setup Instructions

1.  **Install Graphiti**:
    Open your terminal and run the following command to install the Graphiti library:
    ```bash
    pip install graphiti-core
    ```

2.  **Set Up Environment Variables**:
    Graphiti needs to connect to your Neo4j database and use your OpenAI API key. You can set these as environment variables in your terminal.

    *   **OpenAI API Key**:
        ```bash
        export OPENAI_API_KEY='your_openai_api_key'
        ```

    *   **Neo4j Connection Details** (you can usually use the default values):
        ```bash
        export NEO4J_URI='bolt://localhost:7687'
        export NEO4J_USER='neo4j'
        export NEO4J_PASSWORD='password'
        ```
    *Note: You can also create a `.env` file in the root of your project and place these environment variables there. The `tutorial.py` script will automatically load them.*

3.  **Run the Tutorial**:
    Once your environment is set up, you can run the tutorial script:
    ```bash
    python tutorial.py
    ```

## Understanding the Code

The `tutorial.py` script is heavily commented to explain each step in detail. It's divided into the following sections:

1.  **Configuration**: Setting up logging and database connections.
2.  **Initialization**: Connecting to the Neo4j database.
3.  **Adding Episodes**: Adding your data to the graph.
4.  **Basic Search**: Performing a simple search for relationships.
5.  **Center Node Search**: Refining your search for more relevant results.
6.  **Node Search**: Searching for specific entities in your graph.
7.  **Cleanup**: Closing the database connection.

## Next Steps

After you've run the tutorial, feel free to:

-   **Modify the `tutorial.py` script**: Add your own data and ask different questions.
-   **Explore the official documentation**: Dive deeper into Graphiti's features.
-   **Check out the advanced tutorial**: Once you're comfortable with the basics, move on to the `advanced` section of this tutorial to learn about more complex features.
