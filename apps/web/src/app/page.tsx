"use client";

import { useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { CitationList } from "@/components/CitationList";

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

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  trace_id?: string;
  confidence?: string;
  failure?: string | null;
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSend(text: string) {
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      const data = await res.json();
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        citations: data.citations,
        trace_id: data.trace_id,
        confidence: data.confidence,
        failure: data.failure,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Agentic RAG Platform</h1>

      <div className="space-y-4 mb-4">
        {messages.map((m) => (
          <div key={m.id}>
            <ChatMessage message={m} />
            {m.citations && m.citations.length > 0 && <CitationList citations={m.citations} />}
          </div>
        ))}
        {loading && <div className="text-sm text-gray-500">Searching...</div>}
      </div>

      <ChatInput onSend={handleSend} disabled={loading} />
    </main>
  );
}
