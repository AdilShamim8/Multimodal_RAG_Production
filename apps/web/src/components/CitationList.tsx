"use client";

import { useState } from "react";

interface Citation {
  chunk_id: string;
  document_id: string;
  document_title: string;
  page: number | null;
  section: string | null;
  url: string | null;
  snippet: string;
  verified: boolean;
}

export function CitationList({ citations }: { citations: Citation[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="mt-2 ml-4 border-l-2 border-blue-300 pl-3 space-y-1">
      <div className="text-xs font-semibold text-gray-500">Citations ({citations.length})</div>
      {citations.map((c, i) => (
        <div key={c.chunk_id} className="text-xs">
          <button
            onClick={() => setExpanded(expanded === c.chunk_id ? null : c.chunk_id)}
            className="text-blue-600 hover:underline"
          >
            [{i + 1}] {c.document_title}
            {c.page && ` p.${c.page}`}
            {c.section && ` §${c.section}`}
            {!c.verified && <span className="ml-2 text-red-500">(unverified)</span>}
          </button>
          {expanded === c.chunk_id && (
            <div className="mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded text-gray-700 dark:text-gray-300">
              {c.snippet}
              {c.url && (
                <a href={c.url} target="_blank" rel="noopener noreferrer" className="block mt-1 text-blue-500 hover:underline">
                  Open source →
                </a>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
