import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# --- Setup Environment ---
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# 1. Define Data Models (Pydantic)
# ==========================================
class ConceptNode(BaseModel):
    id: str = Field(description="Slugified concept name (e.g., gradient_descent)")
    name: str = Field(description="Display name of the concept")
    my_explanation: str = Field(description="User's own words explaining the concept")

class EdgeRelationship(BaseModel):
    source_id: str = Field(description="The ID of the new concept")
    target_id: str = Field(description="The ID of an existing concept it relates to")
    relationship: str = Field(description="Type of relationship (e.g., DEPENDS_ON, USES_OUTPUT_FROM)")
    reasoning: str = Field(description="Why these concepts are linked")

class GraphUpdate(BaseModel):
    new_node: ConceptNode
    new_edges: List[EdgeRelationship]

# ==========================================
# 2. Initialize NetworkX Graph
# ==========================================
G = nx.DiGraph() # Using a Directed Graph for directional relationships

# Seed the graph with existing knowledge
G.add_node("backpropagation", 
           name="Backpropagation", 
           explanation="Calculates the error at the output layer and works backward to adjust weights.")

# ==========================================
# 3. Define the Linker Agent
# ==========================================
def extract_and_link(raw_text: str, existing_nodes: list) -> GraphUpdate:
    print("--- Running Graph Linker Agent ---")
    
    # Provide the LLM with the context of what the graph currently knows
    context_str = ", ".join(existing_nodes)
    
    prompt = f"""
    You are a Knowledge Graph agent.
    
    Current existing concepts in the graph: [{context_str}]
    
    Task: 
    1. Extract the core Machine Learning concept from the 'New Input'.
    2. Analyze if this new concept relates to any of the 'Current existing concepts'.
    3. Output a strictly formatted JSON object containing the new node details and any connecting edges.
    
    New Input: {raw_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GraphUpdate,
        ),
    )
    return response.parsed

# ==========================================
# 4. Execution & Visualization Flow
# ==========================================
if __name__ == "__main__":
    new_raw_input = """
    Gradient descent is an optimization algorithm used to minimize the loss function in neural networks. 
    It uses the gradients computed during backpropagation to update the weights of the network iteratively.
    """
    
    # Get current node IDs from the graph
    current_nodes = list(G.nodes())
    
    # Run the Agent
    update_result = extract_and_link(new_raw_input, current_nodes)
    print("\n[Graph Update Instructions]")
    print(json.dumps(update_result.model_dump(), indent=2))
    
    # Apply Updates to NetworkX Graph
    new_node = update_result.new_node
    G.add_node(new_node.id, name=new_node.name, explanation=new_node.my_explanation)
    
    for edge in update_result.new_edges:
        # NetworkX edges are added as (source, target, attributes)
        G.add_edge(edge.source_id, edge.target_id, 
                   label=edge.relationship, 
                   reasoning=edge.reasoning)
                   
    print(f"\nGraph now has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # --- Draw the Graph ---
    print("\nGenerating visualization...")
    plt.figure(figsize=(8, 6))
    
    # Generate layout positions for nodes
    pos = nx.spring_layout(G) 
    
    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
    
    # Draw Node Labels (Using the 'name' attribute we stored)
    node_labels = nx.get_node_attributes(G, 'name')
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12, font_weight='bold')
    
    # Draw Edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
    
    # Draw Edge Labels (Using the 'label' attribute we stored)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    
    plt.title("Anchor Knowledge Graph Update")
    plt.axis('off')
    plt.show() # This will pop up a window displaying the graph