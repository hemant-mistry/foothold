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

def extract_and_link(raw_text: str, existing_nodes: list) -> GraphUpdate:
    context_str = "\n".join([f"- {n['name']} (ID: {n['id']}): {n['my_explanation']}" for n in existing_nodes])
    
    prompt = f"""
    Current existing concepts in the user's graph:
    {context_str}
    
    Task: 
    1. Extract core Machine Learning concepts from the 'New Input'.
    2. Analyze relationships between new concepts and existing concepts.
    3. Output a structured JSON containing nodes and connecting edges.
    
    New Input: {raw_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
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