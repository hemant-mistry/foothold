from fastapi import APIRouter, HTTPException
import database
import traceback
from services.llm import extract_and_link, validate_draft
from models.schemas import IngestRequest, IngestResponse, GraphUpdate

router = APIRouter()

@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_notes(request: IngestRequest):
    try:
        # 1. Fetch current graph context
        graph_data = database.get_graph_data()
        existing_nodes = graph_data["nodes"]
        existing_node_ids = {node["id"] for node in existing_nodes}
        
        # 2. Extract & Link
        draft = extract_and_link(request.raw_text, existing_nodes)
        
        # 3. Validate
        verdict = validate_draft(draft)
        
        # 4. GUARDRAIL CHECK: If validation fails, block draft content
        if not verdict.is_correct:
            return IngestResponse(
                draft={"new_nodes": [], "new_edges": []},
                verdict=verdict
            )
        
        # 5. AUTO-RESOLVE EDGES: Filter or clean up edge references if needed,
        # or ensure any edge pointing to an existing node is safely accounted for.
        valid_new_node_ids = {node.id for node in draft.new_nodes}
        all_known_ids = existing_node_ids.union(valid_new_node_ids)
        
        # Filter out edges pointing to completely unknown ghosts, 
        # or map them cleanly so they don't break Pydantic validation.
        filtered_edges = [
            edge for edge in draft.new_edges 
            if edge.source_id in all_known_ids and edge.target_id in all_known_ids
        ]
        draft.new_edges = filtered_edges
        
        return IngestResponse(draft=draft, verdict=verdict)
    except Exception as e:
        traceback.print_exc()
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