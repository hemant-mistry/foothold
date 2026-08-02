import { useState, useCallback } from 'react';
import type { GraphData, IngestResponse } from '../types';

const API_BASE = 'http://localhost:8000/api';

export const useAnchorApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async (): Promise<GraphData | null> => {
    try {
      const res = await fetch(`${API_BASE}/graph`);
      if (!res.ok) throw new Error('Failed to fetch graph data');
      return await res.json();
    } catch (err: any) {
      setError(err.message);
      return null;
    }
  }, []);

  const ingestNotes = async (rawText: string, goal: string): Promise<IngestResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText, goal: goal }), // Added goal here
      });
      if (!res.ok) throw new Error('Ingestion failed');
      return await res.json();
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const confirmDraft = async (draft: IngestResponse['draft']) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(draft),
      });
      if (!res.ok) throw new Error('Failed to commit draft');
      return await res.json();
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };
  
  const wipeGraph = async (): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/graph`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to wipe graph');
      return true;
    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { fetchGraph, ingestNotes, confirmDraft, loading, error, wipeGraph };
};

