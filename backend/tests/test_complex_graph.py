import os
import json
import textwrap
import networkx as nx
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
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
    id: str = Field(description="Slugified concept name (e.g., self_attention)")
    name: str = Field(description="Display name of the concept")
    my_explanation: str = Field(description="User's own words explaining the concept")

class EdgeRelationship(BaseModel):
    source_id: str = Field(description="The ID of the source concept")
    target_id: str = Field(description="The ID of the target concept")
    relationship: str = Field(description="Type of relationship (e.g., SOLVES_BOTTLENECK_OF, OPERATES_ON, USES)")
    reasoning: str = Field(description="Why these concepts are linked based on the text")

class GraphUpdate(BaseModel):
    new_nodes: List[ConceptNode] = Field(description="List of new concepts extracted from the text")
    new_edges: List[EdgeRelationship] = Field(description="List of relationships connecting new nodes to existing ones, or to each other")

# ==========================================
# 2. Initialize Seed Graph (Prior Knowledge)
# ==========================================
G = nx.DiGraph() 

seed_knowledge = [
    ("neural_networks", "Neural Networks", "Interconnected layers of nodes that learn patterns."),
    ("word_embeddings", "Word Embeddings", "Dense vector representations of words where semantic meaning is mapped to geometric space."),
    ("seq2seq_models", "Seq2Seq Models", "Encoder-decoder architectures used for translation, but they suffer from bottlenecks on long sequences due to fixed-length context vectors.")
]

for node_id, name, explanation in seed_knowledge:
    G.add_node(node_id, name=name, explanation=explanation)

# ==========================================
# 3. Define the Linker Agent
# ==========================================
def extract_and_link(raw_text: str, existing_nodes: dict) -> GraphUpdate:
    print("--- Running Complex Graph Linker Agent ---")
    
    # Format existing knowledge for the prompt so the LLM knows what the user already understands
    context_lines = [f"- {data['name']} (ID: {n}): {data['explanation']}" for n, data in existing_nodes.items()]
    context_str = "\n".join(context_lines)
    
    prompt = f"""
    You are a Knowledge Graph extraction agent.
    
    Current existing concepts in the user's graph:
    {context_str}
    
    Task: 
    1. Extract the core Machine Learning concepts from the 'New Input'. There may be more than one.
    2. Analyze how these new concepts relate to the 'Current existing concepts', and how they relate to each other.
    3. Output a strictly formatted JSON object containing the new nodes and all connecting edges.
    
    New Input: {raw_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GraphUpdate,
            temperature=0.1, # Keep it highly deterministic
        ),
    )
    return response.parsed

# ==========================================
# 4. Execution & Visualization Flow
# ==========================================
if __name__ == "__main__":
    # Complex multi-concept input
    new_raw_input = """
    I've been tracing how the Transformer architecture works. Unlike older seq2seq models that process tokens sequentially, 
    Transformers rely entirely on a Self-Attention mechanism. Self-attention looks at the whole sequence of word embeddings 
    at once to weigh the importance of every other word when encoding a specific word. This completely solves the 
    bottleneck issue of passing everything through a single context vector.
    """
    
    # Get current node data
    current_node_data = dict(G.nodes(data=True))
    
    # Run the Agent
    update_result = extract_and_link(new_raw_input, current_node_data)
    print("\n[Graph Update Instructions Extracted by Gemini]")
    print(json.dumps(update_result.model_dump(), indent=2))
    
    # Apply Updates to NetworkX Graph
    for node in update_result.new_nodes:
        G.add_node(node.id, name=node.name, explanation=node.my_explanation)
    
    for edge in update_result.new_edges:
        G.add_edge(edge.source_id, edge.target_id, 
                   label=edge.relationship, 
                   reasoning=edge.reasoning)
                   
    print(f"\nGraph now has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    # --- Draw the Highly Readable Graph ---
    print("\nGenerating visualization...")
    plt.figure(figsize=(14, 10)) # Much larger canvas
    
    # Kamada-Kawai layout spaces things out better based on graph distance
    pos = nx.kamada_kawai_layout(G) 
    
    # Draw Nodes with custom styling
    nx.draw_networkx_nodes(G, pos, node_color='#a0c4ff', node_size=4000, edgecolors='#555555', linewidths=2)
    
    # Wrap text labels so they fit inside/near the nodes cleanly
    node_labels = {}
    for node, data in G.nodes(data=True):
        wrapped_name = "\n".join(textwrap.wrap(data.get('name', node), width=15))
        node_labels[node] = wrapped_name
        
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10, font_weight='bold', font_family='sans-serif')
    
    # Draw Edges with curved arrows to prevent overlap if bidirectional
    nx.draw_networkx_edges(G, pos, edge_color='#666666', arrows=True, arrowsize=25, 
                           connectionstyle='arc3,rad=0.1', width=2)
    
    # Draw Edge Labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    # Clean up edge labels for readability (replace underscores with spaces)
    formatted_edge_labels = {k: v.replace("_", " ") for k, v in edge_labels.items()}
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=formatted_edge_labels, 
                                 font_color='#d62828', font_size=9, font_weight='bold', 
                                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    plt.title("Anchor Knowledge Graph: Self-Attention & Transformers", fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()