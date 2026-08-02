import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from models.schemas import GraphUpdate, ValidationVerdict
# Ensure environment variables are loaded prior to client initialization
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize client with explicit fallback check
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from environment or .env file.")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_and_link(raw_text: str, existing_nodes: list, goal:str) -> GraphUpdate:
    node_glossary = "\n".join([f"- [{n['id']}]: {n['name']}" for n in existing_nodes])
    
    system_prompt = f"""
    You are a strict knowledge graph extraction system.
    
    USER GOAL: "{goal}"
    
    EXISTING GRAPH NODES:
    {node_glossary if node_glossary else "(The graph is currently empty)"}
    
    INSTRUCTIONS:
    1. EXTRACT: Identify concepts and relationships in the provided text that strictly serve the USER GOAL. Ignore off-topic trivia.
    2. REUSE: If a concept in the text matches an concept in the EXISTING GRAPH NODES, you MUST use its existing [node_id] as the source_id or target_id in your edges.
    3. CREATE: If a concept is genuinely new and relevant to the goal, generate a new unique ID for it.
    4. VALIDATE: Ensure every relation explicitly traces back to the source text. Do not hallucinate connections.
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=system_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GraphUpdate,
            temperature=0.1,
        ),
    )
    return response.parsed

def validate_draft(draft: GraphUpdate) -> ValidationVerdict:
    prompt = f"""
    Task: Review this proposed knowledge graph update for correctness. 
    Flag any gaps, logical misunderstandings, or fundamentally flawed relationships.
    
    Draft to evaluate:
    {draft.model_dump_json()}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ValidationVerdict,
            temperature=0.1,
        ),
    )
    return response.parsed