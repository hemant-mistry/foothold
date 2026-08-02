from fastapi import APIRouter, HTTPException
import database
from services.llm import extract_and_link, validate_draft
from models.schemas import IngestRequest, IngestResponse, GraphUpdate

router = APIRouter()

@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_notes(request: IngestRequest):
    try:
        # 1. Fetch current mock context
        graph_data = database.get_graph_data()
        existing_nodes = graph_data["nodes"]
        
        # 2. Extract & Link
        draft = extract_and_link(request.raw_text, existing_nodes)
        
        # 3. Validate
        verdict = validate_draft(draft)
        
        return IngestResponse(draft=draft, verdict=verdict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/confirm")
async def confirm_concept(update: GraphUpdate):
    try:
        # Commit to mock database
        for node in update.new_nodes:
            database.insert_node(node)
        for edge in update.new_edges:
            database.insert_edge(edge)
            
        return {"status": "success", "nodes_added": len(update.new_nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/graph")
async def fetch_graph():
    return database.get_graph_data()