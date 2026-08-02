import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAnchorApi } from "../hooks/useAnchorApi";
import type { IngestResponse } from "../types/index";

interface IngestionPanelProps {
  onGraphUpdate: () => void;
}

export default function IngestionPanel({ onGraphUpdate }: IngestionPanelProps) {
  const [text, setText] = useState("");
  const [draft, setDraft] = useState<IngestResponse | null>(null);
  const [goal, setGoal] = useState("");
  const { ingestNotes, confirmDraft, loading, error, wipeGraph } =
    useAnchorApi();

  const handleIngest = async () => {
    if (!text.trim() || !goal.trim()) return;
    const res = await ingestNotes(text, goal);
    if (res) setDraft(res);
  };

  const handleConfirm = async () => {
    if (!draft) return;
    await confirmDraft(draft.draft);
    setDraft(null);
    setText("");
    onGraphUpdate(); // Refresh the main graph
  };

  const handleWipe = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to completely wipe the graph database? This cannot be undone.",
    );
    if (!confirmed) return;

    const success = await wipeGraph();
    if (success) {
      setDraft(null);
      setText("");
      onGraphUpdate(); // Trigger a re-fetch to clear the canvas
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800 tracking-tight">
          Expand Knowledge
        </h2>
        <button
          onClick={handleWipe}
          disabled={loading}
          className="text-xs font-semibold text-red-600 hover:text-white border border-red-200 hover:bg-red-500 hover:border-red-500 py-1.5 px-3 rounded-lg transition-all shadow-sm disabled:opacity-50"
          title="Wipe database memory"
        >
          Wipe Graph
        </button>
      </div>

      {/* Goal Setting Section */}
      <div className="mb-4 flex flex-col gap-2">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Extraction Goal
        </label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="What should this graph focus on?"
          className="w-full p-3 text-sm border border-gray-200 rounded-xl shadow-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-700 bg-gray-50 focus:bg-white"
          rows={2}
          disabled={loading || !!draft}
        />
      </div>

      <div className="flex-1 flex flex-col gap-2">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Raw Notes
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your notes, transcript, or ideas here..."
          className="flex-1 w-full p-4 border border-gray-200 rounded-xl shadow-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-gray-700 leading-relaxed"
          disabled={loading || !!draft}
        />

        <AnimatePresence mode="popLayout">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="mt-2 p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-200"
            >
              {error}
            </motion.div>
          )}

          {draft && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 bg-white border border-gray-200 rounded-xl p-4 shadow-sm"
            >
              <div className="mb-4">
                <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                  {draft.verdict.is_correct
                    ? "✅ Validation Passed"
                    : "⚠️ Structural Issues"}
                </h3>
                {!draft.verdict.is_correct && (
                  <p className="text-sm text-red-600 mt-1">
                    {draft.verdict.failure_reason}
                  </p>
                )}
              </div>

              <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {draft.draft.new_nodes.map((n) => (
                  <div
                    key={n.id}
                    className="text-sm bg-gray-50 p-2 rounded-md border border-gray-100"
                  >
                    <span className="font-semibold text-blue-600">
                      +{n.name}
                    </span>
                    : {n.my_explanation}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-6 flex gap-3">
        {!draft ? (
          <button
            onClick={handleIngest}
            disabled={loading || !text.trim() || !goal.trim()}
            className="w-full bg-slate-900 text-white font-medium py-3 px-4 rounded-xl shadow-md hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex justify-center items-center"
          >
            {loading ? "Analyzing..." : "Extract Concepts"}
          </button>
        ) : (
          <>
            <button
              onClick={() => setDraft(null)}
              disabled={loading}
              className="flex-1 bg-white text-gray-600 border border-gray-200 font-medium py-3 px-4 rounded-xl hover:bg-gray-50 transition-colors"
            >
              Discard
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading || !draft.verdict.is_correct}
              className="flex-1 bg-blue-600 text-white font-medium py-3 px-4 rounded-xl shadow-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Saving..." : "Commit to Graph"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
