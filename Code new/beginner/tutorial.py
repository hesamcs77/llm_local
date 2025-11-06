# Welcome to the Graphiti Beginner Tutorial!
# This tutorial will walk you through the basics of using the Graphiti library.
# We'll cover connecting to a database, adding data, and performing basic searches.
# This file is a heavily commented version of the quickstart_neo4j.py example.

# Import necessary libraries
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from logging import INFO

# dotenv is used to load environment variables from a .env file
from dotenv import load_dotenv

# Import the main Graphiti class and other components
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

#################################################
# SECTION 1: CONFIGURATION
#################################################
# In this section, we set up logging and load environment
# variables for connecting to our Neo4j graph database.
# A graph database is a type of database that uses graph
# structures for semantic queries with nodes, edges, and properties
# to represent and store data.
#################################################

# Configure logging to display informative messages
logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file in your project root.
# This is a secure way to manage sensitive information like API keys.
load_dotenv()

# Get Neo4j connection parameters from environment variables.
# We provide default values for convenience.
# Make sure your Neo4j Desktop application is running.
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

# Check if the Neo4j connection details are provided.
if not neo4j_uri or not neo4j_user or not neo4j_password:
    raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')


# We use an async main function because Graphiti is an asynchronous library.
# This allows for efficient I/O operations, especially when dealing with databases.
async def main():
    #################################################
    # SECTION 2: INITIALIZATION
    #################################################
    # Here, we connect to the Neo4j database and initialize
    # the Graphiti library. This step is crucial before
    # you can perform any other operations.
    #################################################

    # Create a Graphiti instance with your Neo4j connection details.
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)

    try:
        #################################################
        # SECTION 3: ADDING EPISODES
        #################################################
        # "Episodes" are the fundamental units of information in Graphiti.
        # They can be simple text or structured JSON data.
        # Graphiti automatically processes these episodes to
        # extract entities (nodes) and their relationships (edges).
        #################################################

        # Let's create a list of episodes to add to our knowledge graph.
        episodes = [
            {
                'content': 'Kamala Harris is the Attorney General of California. She was previously '
                'the district attorney for San Francisco.',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': 'As AG, Harris was in office from January 3, 2011 – January 3, 2017',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'state': 'California',
                    'previous_role': 'Lieutenant Governor',
                    'previous_location': 'San Francisco',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'term_start': 'January 7, 2019',
                    'term_end': 'Present',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
        ]

        # Now, let's add these episodes to the graph one by one.
        for i, episode in enumerate(episodes):
            await graphiti.add_episode(
                name=f'Freakonomics Radio {i}',
                episode_body=episode['content']
                if isinstance(episode['content'], str)
                else json.dumps(episode['content']),
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
            )
            print(f'Added episode: Freakonomics Radio {i} ({episode["type"].value})')

        #################################################
        # SECTION 4: BASIC SEARCH (EDGE SEARCH)
        #################################################
        # The most straightforward way to query your knowledge
        # graph is by searching for relationships (edges).
        # Graphiti's `search` method uses a "hybrid" approach,
        # combining semantic (meaning-based) search with
        # traditional keyword (BM25) search for best results.
        #################################################

        # Let's ask a question to our knowledge graph.
        print("\nSearching for: 'Who was the California Attorney General?'")
        results = await graphiti.search('Who was the California Attorney General?')

        # Let's print the facts we found.
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}') # Unique ID for the fact
            print(f'Fact: {result.fact}') # The extracted fact
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')

        #################################################
        # SECTION 5: CENTER NODE SEARCH (ADVANCED EDGE SEARCH)
        #################################################
        # To get more contextually relevant results, you can
        # specify a "center node." This tells Graphiti to
        # prioritize results that are closely related to a
        # particular entity in the graph.
        #################################################

        if results and len(results) > 0:
            # We'll use the source node of our first search result as the center node.
            center_node_uuid = results[0].source_node_uuid

            print('\nReranking search results based on graph distance:')
            print(f'Using center node UUID: {center_node_uuid}')

            # Perform the search again, this time with the center node.
            reranked_results = await graphiti.search(
                'Who was the California Attorney General?', center_node_uuid=center_node_uuid
            )

            # Print the reranked results.
            print('\nReranked Search Results:')
            for result in reranked_results:
                print(f'UUID: {result.uuid}')
                print(f'Fact: {result.fact}')
                if hasattr(result, 'valid_at') and result.valid_at:
                    print(f'Valid from: {result.valid_at}')
                if hasattr(result, 'invalid_at') and result.invalid_at:
                    print(f'Valid until: {result.invalid_at}')
                print('---')
        else:
            print('No results found in the initial search to use as center node.')

        #################################################
        # SECTION 6: NODE SEARCH USING SEARCH RECIPES
        #################################################
        # Besides searching for edges (relationships), you can
        # also search directly for nodes (entities). Graphiti
        # provides pre-configured "search recipes" for common
        # search scenarios. Here, we'll use one to find nodes.
        #################################################

        print(
            '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
        )

        # Copy a predefined search recipe and customize it.
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5  # We only want the top 5 results.

        # Execute the node search.
        node_search_results = await graphiti._search(
            query='California Governor',
            config=node_search_config,
        )

        # Print the details of the nodes we found.
        print('\nNode Search Results:')
        for node in node_search_results.nodes:
            print(f'Node UUID: {node.uuid}')
            print(f'Node Name: {node.name}')
            node_summary = node.summary[:100] + '...' if len(node.summary) > 100 else node.summary
            print(f'Content Summary: {node_summary}')
            print(f'Node Labels: {", ".join(node.labels)}')
            print(f'Created At: {node.created_at}')
            if hasattr(node, 'attributes') and node.attributes:
                print('Attributes:')
                for key, value in node.attributes.items():
                    print(f'  {key}: {value}')
            print('---')

    finally:
        #################################################
        # SECTION 7: CLEANUP
        #################################################
        # It's very important to close the connection to
        # the database when you're done. This releases
        # resources and ensures the application exits cleanly.
        #################################################

        await graphiti.close()
        print('\nConnection closed')


# This is the standard Python entry point.
if __name__ == '__main__':
    asyncio.run(main())
