import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAnchorApi } from './hooks/useAnchorApi'
import type { GraphData } from './types/index';
import GraphCanvas from './components/GraphCanvas';
import './index.css'
import IngestionPanel from './components/IngestionPanel';

export default function App() {
  const { fetchGraph, loading } = useAnchorApi();
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });

  const loadData = async () => {
    const data = await fetchGraph();
    if (data) setGraphData(data);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="h-screen w-screen bg-gray-50 flex flex-col font-sans overflow-hidden">
      {/* Top Navbar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 py-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold shadow-sm">
            A
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-800">Anchor</h1>
        </div>
        <div className="text-xs font-medium bg-gray-100 text-gray-500 px-3 py-1.5 rounded-full border border-gray-200">
          {graphData.nodes.length} Nodes Indexed
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: Sidebar */}
        <motion.aside 
          initial={{ x: -300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="w-full max-w-md bg-white border-r border-gray-200 p-6 flex flex-col z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)] relative"
        >
          <IngestionPanel onGraphUpdate={loadData} />
        </motion.aside>

        {/* Right Panel: Force-Directed Graph */}
        <motion.section 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex-1 relative"
        >
          {graphData.nodes.length > 0 ? (
            <GraphCanvas data={graphData} />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-slate-400 font-medium">
              {loading ? 'Initializing workspace...' : 'Graph is empty. Start by ingesting some notes.'}
            </div>
          )}
        </motion.section>
      </main>
    </div>
  );
}