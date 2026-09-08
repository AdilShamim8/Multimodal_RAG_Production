"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  trace_id?: string;
  confidence?: string;
  failure?: string | null;
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`rounded-lg p-3 ${isUser ? "bg-blue-50 dark:bg-blue-900/20 ml-auto max-w-prose" : "bg-gray-50 dark:bg-gray-800/50"}`}>
      <div className="text-xs font-semibold mb-1 text-gray-500">
        {isUser ? "You" : "Assistant"}
        {!isUser && message.confidence && (
          <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-200 dark:bg-gray-700">
            {message.confidence}
          </span>
        )}
      </div>
      <div className="prose prose-sm dark:prose-invert max-w-none">
        {isUser ? <p>{message.content}</p> : <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>}
      </div>
      {!isUser && message.trace_id && (
        <div className="mt-2 text-xs text-gray-400">trace: {message.trace_id.slice(0, 8)}</div>
      )}
      {!isUser && message.failure && (
        <div className="mt-2 text-xs text-red-500">failure: {message.failure}</div>
      )}
    </div>
  );
}
