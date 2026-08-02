export type MasteryLevel = 'solid' | 'fresh' | 'needs_review';

export interface ConceptNode {
  id: string;
  name: string;
  my_explanation: string;
  mastery: MasteryLevel;
  version: number;
}

export interface EdgeRelationship {
  source_id: string;
  target_id: string;
  relationship: string;
  reasoning: string;
}

export interface GraphData {
  nodes: ConceptNode[];
  edges: EdgeRelationship[];
}

export interface ValidationVerdict {
  is_correct: boolean;
  failure_reason: string | null;
}

export interface IngestResponse {
  draft: {
    new_nodes: ConceptNode[];
    new_edges: EdgeRelationship[];
  };
  verdict: ValidationVerdict;
}