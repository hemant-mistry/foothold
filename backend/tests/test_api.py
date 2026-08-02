import pytest
from fastapi.testclient import TestClient
from main import app
import database

# Initialize the TestClient
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_mock_db():
    """Clear the mock database before each test to ensure isolation."""
    database.MOCK_NODES.clear()
    database.MOCK_EDGES.clear()

def test_simple_ingestion():
    """
    Test 1 (Simple): A straightforward, single concept with no prior graph context.
    The LLM should extract at least one node and return a valid verdict.
    """
    raw_text = "I just learned about Linear Regression. It's a method to predict a target variable by fitting the best straight line through the data points."
    
    response = client.post("/api/ingest", json={"raw_text": raw_text})
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert Valid Verdict
    assert data["verdict"]["is_correct"] is True
    
    # Assert Node Extraction (Allowing for >1 if LLM extracts sub-concepts like 'Target Variable')
    nodes = data["draft"]["new_nodes"]
    assert len(nodes) >= 1
    
    # Verify 'Linear Regression' is among the extracted nodes
    node_ids = [node["id"].lower() for node in nodes]
    assert any("linear" in n_id for n_id in node_ids)

def test_medium_ingestion_with_relationships():
    """
    Test 2 (Medium): Introduce a new concept that builds on prior knowledge.
    We seed the mock DB first, then ingest. The LLM must find the relationship.
    """
    # 1. Seed the DB with prior knowledge (Fixed Pydantic Validation by adding my_analogies)
    from models.schemas import ConceptNode
    database.insert_node(ConceptNode(
        id="linear_regression", 
        name="Linear Regression", 
        my_explanation="Predicting a target variable using a straight line.",
        my_analogies=[] 
    ))
    
    # 2. Ingest new related knowledge
    raw_text = "Logistic Regression is actually quite similar to Linear Regression, but instead of predicting a continuous number, it uses a sigmoid function to output a probability between 0 and 1 for classification."
    
    response = client.post("/api/ingest", json={"raw_text": raw_text})
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert Node Extraction
    nodes = data["draft"]["new_nodes"]
    assert len(nodes) >= 1
    node_ids = [node["id"].lower() for node in nodes]
    assert any("logistic" in n_id for n_id in node_ids)
    
    # Assert Relationship Discovery
    edges = data["draft"]["new_edges"]
    assert len(edges) >= 1
    
    # Verify the edge links the new concept back to the seeded concept
    edge_targets = [edge["target_id"] for edge in edges] + [edge["source_id"] for edge in edges]
    assert "linear_regression" in edge_targets

def test_extremely_hard_ingestion_with_hallucination_catch():
    """
    Test 3 (Extremely Hard): Deliberately flawed logic.
    We feed the system a structurally incorrect analogy. 
    The Validation Agent MUST catch it and flag it as incorrect.
    """
    # 1. Seed the DB (Fixed Pydantic Validation by adding my_analogies)
    from models.schemas import ConceptNode
    database.insert_node(ConceptNode(
        id="decision_trees", 
        name="Decision Trees", 
        my_explanation="A model that splits data based on feature values to make a prediction.",
        my_analogies=[]
    ))
    
    # 2. Ingest intentionally flawed knowledge
    flawed_text = """
    Random Forests are a type of ensemble model. It works exactly like a single Decision Tree, 
    except instead of splitting the data, it just copies the exact same tree 100 times and asks 
    them all the same question. It's like asking 100 clones of myself for advice; they will all 
    give the exact same answer, but somehow that makes the prediction better.
    """
    
    response = client.post("/api/ingest", json={"raw_text": flawed_text})
    assert response.status_code == 200
    
    data = response.json()
    verdict = data["verdict"]
    
    # The Validation Agent should flag this as structurally unsound
    assert verdict["is_correct"] is False
    assert verdict["failure_reason"] is not None