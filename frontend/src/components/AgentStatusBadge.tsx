'use client';

import React from 'react';

interface AgentStatusBadgeProps {
  retrievalIterations: number;
}

export default function AgentStatusBadge({ retrievalIterations }: AgentStatusBadgeProps) {
  if (retrievalIterations <= 1) return null;

  return (
    <div className="w-full flex items-center gap-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 p-3.5 rounded-2xl shadow-md">
      <svg className="w-5 h-5 flex-shrink-0 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
      </svg>
      <div className="text-sm">
        <span className="font-bold">Search broadened:</span> Initial results were sparse. The AI Agent automatically relaxed some filters (such as color or material) to retrieve more items.
      </div>
    </div>
  );
}
