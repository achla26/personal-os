"use client";

import ItemCard from "./ItemCard";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  items?: any[];
  status: "sending" | "sent" | "error";
}

interface ChatTimelineProps {
  messages: ChatMessage[];
  onDoneItem?: (itemId: number) => void;
  onRetry?: (messageId: string) => void;
}

export default function ChatTimeline({
  messages,
  onDoneItem,
  onRetry,
}: ChatTimelineProps) {
  return (
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto px-4 py-6">
      {messages.length === 0 && (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-content-tertiary">
            Throw anything at me...
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex flex-col ${
            msg.role === "user" ? "items-end" : "items-start"
          }`}
        >
          {/* User message (Purple bubble like mockup) */}
          {msg.role === "user" && (
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm font-medium leading-relaxed ${
                msg.status === "error"
                  ? "border border-danger bg-danger/10 text-danger"
                  : msg.status === "sending"
                  ? "bg-surface-2 text-content-tertiary"
                  : "bg-[#6366f1] text-white shadow-lg"
              }`}
            >
              {msg.content}
              {msg.status === "error" && onRetry && (
                <button
                  onClick={() => onRetry(msg.id)}
                  className="ml-2 text-xs font-bold underline"
                >
                  Retry
                </button>
              )}
            </div>
          )}

          {/* Assistant response with "Filed X things" pill */}
          {msg.role === "assistant" && (
            <div className="flex w-full flex-col gap-2.5">
              {msg.status === "sending" && (
                <p className="text-xs text-content-tertiary animate-pulse pl-1">
                  soch raha hoon...
                </p>
              )}

              {msg.items && msg.items.length > 0 && (
                <>
                  <div className="mb-1 self-start rounded-full bg-surface-2 px-3 py-1 text-xs font-medium text-content-secondary border border-border-subtle">
                    Filed {msg.items.length} {msg.items.length === 1 ? "thing" : "things"} 👇
                  </div>

                  {msg.items.map((item) => (
                    <ItemCard
                      key={item.id}
                      item={item}
                      onDone={onDoneItem}
                    />
                  ))}
                </>
              )}

              {msg.status === "error" && (
                <p className="text-xs text-danger pl-1">
                  didn&apos;t get could you please tell me again
                </p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}