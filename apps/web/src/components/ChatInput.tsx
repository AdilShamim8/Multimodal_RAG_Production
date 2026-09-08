"use client";

import { useState, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  }

  return (
    <div className="flex gap-2">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question..."
        rows={2}
        className="flex-1 rounded border border-gray-300 p-2 text-sm dark:bg-gray-800 dark:border-gray-600"
        disabled={disabled}
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
