# Welcome to the Graphiti Advanced Tutorial!
# This tutorial demonstrates how to build a conversational sales agent
# using Graphiti and LangGraph.
# You'll learn how to integrate Graphiti into a larger AI application
# to create personalized, context-aware experiences.

# Import necessary libraries
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

# Import Graphiti components
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
)
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

# Load environment variables
load_dotenv()

#################################################
# SECTION 1: CONFIGURATION
#################################################
# As with the beginner tutorial, we start by setting up
# our environment, logging, and database connections.
#################################################


def setup_logging():
    logger = logging.getLogger()
    # Set the root logger level to ERROR to suppress noisy library logs
    logger.setLevel(logging.ERROR)
    # Configure a handler for our application's logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Capture INFO level and above
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # Add the handler to the root logger
    logger.addHandler(console_handler)
    return logging.getLogger(__name__)


logger = setup_logging()

# --- LangSmith Integration (Optional) ---
# If you want to trace your agent's execution with LangSmith,
# set your LANGSMITH_API_KEY and uncomment the following line.
# os.environ['LANGCHAIN_TRACING_V2'] = 'true'
# os.environ['LANGCHAIN_PROJECT'] = 'Graphiti Advanced Tutorial'

# --- Graphiti Configuration ---
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

# Initialize the Graphiti client
client = Graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
)

#################################################
# SECTION 2: DATA INGESTION AND SETUP
#################################################
# In a real-world application, you would load your data
# into Graphiti. Here, we'll load a product catalog
# and create a user profile in the graph.
#################################################


async def setup_database():
    """
    Initializes the database. Wipes existing data, builds indices,
    ingests product data, and creates a user node.
    IMPORTANT: This is a destructive operation.
    """
    logger.info('Setting up the database. This may take a moment...')
    logger.warning('This will clear all existing data in the graph!')

    # 1. Clear existing data and build schema
    await clear_data(client.driver)
    await client.build_indices_and_constraints()
    logger.info('Database cleared and schema built.')

    # 2. Ingest product data from a JSON file
    script_dir = Path(__file__).parent.parent.parent / 'examples' / 'data'
    json_file_path = script_dir / 'manybirds_products.json'

    if not json_file_path.exists():
        logger.error(f'Product data not found at {json_file_path}')
        return None, None

    with open(json_file_path) as file:
        products = json.load(file)['products']

    for i, product in enumerate(products):
        await client.add_episode(
            name=product.get('title', f'Product {i}'),
            episode_body=str({k: v for k, v in product.items() if k != 'images'}),
            source_description='ManyBirds products',
            source=EpisodeType.json,
            reference_time=datetime.now(timezone.utc),
        )
    logger.info(f'{len(products)} products ingested.')

    # 3. Create a user node for personalization
    user_name = 'jess'
    await client.add_episode(
        name='User Creation',
        episode_body=f'{user_name} is interested in buying a pair of shoes',
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc),
        source_description='SalesBot',
    )

    # 4. Retrieve UUIDs for the user and the product brand
    user_node_list = await client._search(
        user_name, NODE_HYBRID_SEARCH_EPISODE_MENTIONS
    )
    user_node_uuid = user_node_list.nodes[0].uuid

    manybirds_node_list = await client._search(
        'ManyBirds', NODE_HYBRID_SEARCH_EPISODE_MENTIONS
    )
    manybirds_node_uuid = manybirds_node_list.nodes[0].uuid
    logger.info('User node and brand node created.')

    return user_node_uuid, manybirds_node_uuid


#################################################
# SECTION 3: CREATING THE LANGGRAPH AGENT
#################################################
# Now we'll define the components of our conversational agent.
# This includes tools, state, and the main agent logic.
#################################################

# --- Helper Function ---
def edges_to_facts_string(entities: list[EntityEdge]):
    """Converts a list of graph edges to a simple string format."""
    return '- ' + '\\n- '.join([edge.fact for edge in entities])


# --- LangGraph State ---
class State(TypedDict):
    """Defines the state of our agent's conversation."""

    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str
    manybirds_node_uuid: str


# --- Agent Tool ---
@tool
async def get_shoe_data(query: str, state: State) -> str:
    """Search the graph for information about shoes and related products."""
    logger.info(f'Tool `get_shoe_data` called with query: {query}')
    edge_results = await client.search(
        query,
        center_node_uuid=state['manybirds_node_uuid'],  # Focus search on products
        num_results=10,
    )
    return edges_to_facts_string(edge_results)


tools = [get_shoe_data]
tool_node = ToolNode(tools)

# --- LLM Configuration ---
llm = ChatOpenAI(model='gpt-4.1-mini', temperature=0).bind_tools(tools)


# --- Main Agent Logic (Chatbot Node) ---
async def chatbot(state: State):
    """
    This is the core of our agent. It retrieves context from Graphiti,
    constructs a prompt, calls the LLM, and persists the conversation back to the graph.
    """
    logger.info('Chatbot node is executing.')
    facts_string = None
    if len(state['messages']) > 0:
        last_message = state['messages'][-1]
        graphiti_query = (
            f'{"SalesBot" if isinstance(last_message, AIMessage) else state["user_name"]}: '
            f'{last_message.content}'
        )

        # Search Graphiti using the user's UUID as the center node.
        # This personalizes the context by prioritizing facts related to the user.
        edge_results = await client.search(
            graphiti_query, center_node_uuid=state['user_node_uuid'], num_results=5
        )
        facts_string = edges_to_facts_string(edge_results)
        logger.info(f'Retrieved facts for context: \\n{facts_string}')

    # Construct the system prompt with the retrieved facts.
    system_message = SystemMessage(
        content=f"""You are a skillful shoe salesperson for ManyBirds. Review the user info and conversation history below to respond.
        Keep responses concise. Your goal is to be helpful and make a sale.

        Key info to gather:
        - Shoe size
        - Specific needs (e.g., wide feet)
        - Preferred colors and styles
        - Budget

        Ask for this info if you don't have it.

        Facts about the user and their conversation:
        {facts_string or 'No facts about the user and their conversation'}"""
    )

    messages = [system_message] + state['messages']
    response = await llm.ainvoke(messages)
    logger.info(f'LLM generated response: {response.content}')

    # Asynchronously add the conversation turn to the graph.
    # This enriches the knowledge graph for future interactions.
    asyncio.create_task(
        client.add_episode(
            name='Chatbot Response',
            episode_body=(
                f'{state["user_name"]}: {state["messages"][-1].content}\\n'
                f'SalesBot: {response.content}'
            ),
            source=EpisodeType.message,
            reference_time=datetime.now(timezone.utc),
            source_description='Chatbot',
        )
    )

    return {'messages': [response]}


#################################################
# SECTION 4: DEFINING THE GRAPH STRUCTURE
#################################################
# We'll now define the flow of our application using a StateGraph.
# This determines how the agent, tools, and logic connect.
#################################################


async def should_continue(state, config):
    """Determines whether to call a tool or end the turn."""
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return 'end'  # No tool call, so we're done.
    else:
        return 'continue'  # Tool call detected, so continue to the tool node.


# --- Build the Graph ---
graph_builder = StateGraph(State)
memory = MemorySaver()

# Add nodes
graph_builder.add_node('agent', chatbot)
graph_builder.add_node('tools', tool_node)

# Define edges
graph_builder.add_edge(START, 'agent')
graph_builder.add_conditional_edges(
    'agent', should_continue, {'continue': 'tools', 'end': END}
)
graph_builder.add_edge('tools', 'agent')

# Compile the graph
graph = graph_builder.compile(checkpointer=memory)


#################################################
# SECTION 5: RUNNING THE AGENT
#################################################
# Finally, we'll run the agent in a loop to create an
# interactive command-line chat experience.
#################################################


async def main():
    """Main function to set up and run the chatbot."""
    # This setup is slow, so we only run it if needed.
    # In a real app, you'd have a separate script for data ingestion.
    run_setup = input(
        'Do you want to run the initial database setup? (yes/no) '
        'This will wipe your database. \\n'
    )
    if run_setup.lower() == 'yes':
        user_uuid, manybirds_uuid = await setup_database()
        if user_uuid is None:
            return
    else:
        # If not setting up, try to retrieve existing nodes
        try:
            user_node_list = await client._search(
                'jess', NODE_HYBRID_SEARCH_EPISODE_MENTIONS
            )
            user_uuid = user_node_list.nodes[0].uuid
            manybirds_node_list = await client._search(
                'ManyBirds', NODE_HYBRID_SEARCH_EPISODE_MENTIONS
            )
            manybirds_uuid = manybirds_node_list.nodes[0].uuid
            logger.info('Existing user and brand nodes found.')
        except (IndexError, AttributeError):
            logger.error(
                'Could not find existing user/brand nodes. '
                'Please run the setup by answering "yes".'
            )
            return

    # Configuration for our chat session
    config = {'configurable': {'thread_id': uuid.uuid4().hex}}
    user_state = {
        'user_name': 'jess',
        'user_node_uuid': user_uuid,
        'manybirds_node_uuid': manybirds_uuid,
    }

    print("\\n--- ShoeBot is ready! ---")
    print("Type 'exit' to end the conversation.")
    print("Hello, how can I help you find shoes today?")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        graph_state = {
            'messages': [{'role': 'user', 'content': user_input}],
            **user_state,
        }

        print("Assistant: ", end="", flush=True)
        try:
            async for event in graph.astream(graph_state, config=config):
                for value in event.values():
                    if 'messages' in value:
                        last_message = value['messages'][-1]
                        if isinstance(last_message, AIMessage) and isinstance(
                            last_message.content, str
                        ):
                            print(last_message.content, end="", flush=True)
            print()  # Newline after assistant's full response
        except Exception as e:
            print(f'An error occurred: {e}')

    await client.close()
    print("\\n--- Conversation ended ---")


if __name__ == '__main__':
    asyncio.run(main())
