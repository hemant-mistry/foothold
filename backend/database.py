import sqlite3
from pathlib import Path
from models.schemas import ConceptNode, EdgeRelationship

# Creates the DB file in the backend directory
DB_PATH = Path(__file__).resolve().parent / "foothold_graph.db"

def get_db():
    """Returns a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the append-only SQLite schema."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                my_explanation TEXT NOT NULL,
                mastery TEXT DEFAULT 'fresh',
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT,
                target_id TEXT,
                relationship TEXT NOT NULL,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_id, target_id, relationship),
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )
        """)
        conn.commit()

def get_graph_data() -> dict:
    """Fetches the entire graph for the UI and LLM context."""
    with get_db() as conn:
        nodes = [dict(row) for row in conn.execute("SELECT * FROM nodes").fetchall()]
        edges = [dict(row) for row in conn.execute("SELECT * FROM edges").fetchall()]
    return {"nodes": nodes, "edges": edges}

def insert_node(node: ConceptNode):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO nodes (id, name, my_explanation) 
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET 
                name=excluded.name, 
                my_explanation=excluded.my_explanation,
                version=version+1
        """, (node.id, node.name, node.my_explanation))
        conn.commit()

def insert_edge(edge: EdgeRelationship):
    with get_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO edges (source_id, target_id, relationship, reasoning) 
            VALUES (?, ?, ?, ?)
        """, (edge.source_id, edge.target_id, edge.relationship, edge.reasoning))
        conn.commit()