from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

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


class EdgeRelationship(BaseModel):
    source_id: str
    target_id: str 
    relationship: str
    reasoning: str

class GraphUpdate(BaseModel):
    new_nodes: List[ConceptNode]
    new_edges: List[EdgeRelationship]

class IngestRequest(BaseModel):
    raw_text: str

class IngestResponse(BaseModel):
    draft: GraphUpdate
    verdict: ValidationVerdict

