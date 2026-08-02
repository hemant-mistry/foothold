import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file (looks for backend/.env or root .env)
env_path = Path(__file__).resolve().parent.parent / ".env"  # Points to backend/.env
load_dotenv(dotenv_path=env_path)

from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# ==========================================
# 1. Define Data Models (Pydantic)
# ==========================================
class MasteryLevel(str, Enum):
    solid = "solid"
    fresh = "fresh"
    needs_review = "needs_review"

class ConceptNode(BaseModel):
    id: str = Field(description="Slugified concept name")
    name: str = Field(description="Display name of the concept")
    my_explanation: str = Field(description="User's own words explaining the concept")
    my_analogies: List[str] = Field(description="User's own comparisons")
    mastery: MasteryLevel = MasteryLevel.fresh
    version: int = 1

class ValidationVerdict(BaseModel):
    is_correct: bool = Field(description="Whether the extracted understanding is structurally correct.")
    failure_reason: Optional[str] = Field(description="Specific reason for failure or flagged gaps, if any.")
    flagged_analogies: List[str] = Field(description="Any analogies that are structurally unsound.")

# ==========================================
# 2. Mock Data (The "Input")
# ==========================================
mock_notes = """
I was reading about Neural Networks today, specifically Backpropagation. 
Basically, it's how the network learns from its mistakes. It calculates the error at the output layer 
and then works backward through the hidden layers to adjust the weights of the connections.
It feels analogous to a manager at a factory finding a defective product at the end of the line, 
and then walking backward down the assembly line, yelling at each worker based on how much they contributed to the defect, 
so they know to adjust their process for the next item.
"""

mock_db_context = """
Existing Database Context for the User:
- Knows: "Neural Networks" (Basic concept of layers and weights)
- Knows: "Loss Function" (How error is calculated)
- Analogies previously used: "Weights are like volume knobs on an audio mixer."
"""

# ==========================================
# 3. Agent Functions
# ==========================================
def extract_concept_draft(client: genai.Client, raw_text: str, context: str) -> ConceptNode:
    print("--- Running Extractor Agent ---")
    prompt = f"""
    Context: {context}
    
    Task: Extract the core Machine Learning concept and the user's analogies from the following notes.
    Output strictly as a JSON object matching the requested schema.
    
    Notes: {raw_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ConceptNode,
        ),
    )
    # The SDK automatically parses the JSON back into the Pydantic class
    return response.parsed 

def validate_draft(client: genai.Client, draft: ConceptNode) -> ValidationVerdict:
    print("--- Running Validator Agent ---")
    prompt = f"""
    Task: Review this ML concept understanding for correctness. 
    Evaluate if the explanation is accurate and if the analogy used is structurally sound for the concept.
    Flag any gaps, misunderstandings, or bad analogies.
    
    Draft to evaluate:
    {draft.model_dump_json()}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ValidationVerdict,
        ),
    )
    return response.parsed

# ==========================================
# 4. Execution Flow
# ==========================================
if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        exit(1)
        
    client = genai.Client() 
    
    try:
        # Step 1: Extraction
        draft_node = extract_concept_draft(client, mock_notes, mock_db_context)
        print("\n[Extraction Result]")
        print(json.dumps(draft_node.model_dump(), indent=2))
        
        # Step 2: Validation
        verdict = validate_draft(client, draft_node)
        print("\n[Validation Result]")
        print(json.dumps(verdict.model_dump(), indent=2))
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")