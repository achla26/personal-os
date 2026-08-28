"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import ChatTimeline, { ChatMessage } from "@/components/ChatTimeline";
import ChatComposer from "@/components/ChatComposer";

export default function ChatScreen() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auth Protection Check
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  const handleSendMessage = async (text: string) => {
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;

    // 1. Optimistic Updates: add user message & assistant pending state immediately
    const newUserMsg: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: text,
      status: "sending",
    };

    const newAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      status: "sending",
    };

    setMessages((prev) => [...prev, newUserMsg, newAssistantMsg]);
    setIsSending(true);

    try {
      // 2. Call backend /chat orchestrator
      const response = await apiFetch<{ message_id: number; items: any[] }>("/chat", {
        method: "POST",
        body: { text: text } as any,
      });

      // 3. Update states with server response
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === userMsgId) {
            return { ...msg, status: "sent" };
          }
          if (msg.id === assistantMsgId) {
            return {
              ...msg,
              status: "sent",
              items: response.items || [],
            };
          }
          return msg;
        })
      );
    } catch (error: any) {
      // 4. Mark failure state for both bubbles
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === userMsgId || msg.id === assistantMsgId) {
            return { ...msg, status: "error" };
          }
          return msg;
        })
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleRetry = (messageId: string) => {
    const targetMsg = messages.find((m) => m.id === messageId);
    if (!targetMsg) return;

    // Filter out the failed message pair and re-trigger send
    setMessages((prev) => prev.filter((m) => m.id !== messageId && !m.id.startsWith("asst-")));
    handleSendMessage(targetMsg.content);
  };

  const handleDoneItem = async (itemId: number) => {
    // 1. Optimistic Update: mark item as done in state instantly
    setMessages((prev) =>
      prev.map((msg) => {
        if (!msg.items) return msg;
        return {
          ...msg,
          items: msg.items.map((item) =>
            item.id === itemId ? { ...item, status: "done" } : item
          ),
        };
      })
    );

    try {
      // 2. Update DB status in background
      await apiFetch(`/items/${itemId}`, {
        method: "PATCH",
        body: { status: "done" } as any,
      });
    } catch (err) {
      // Revert if network/server fails
      setMessages((prev) =>
        prev.map((msg) => {
          if (!msg.items) return msg;
          return {
            ...msg,
            items: msg.items.map((item) =>
              item.id === itemId ? { ...item, status: "pending" } : item
            ),
          };
        })
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-0">
        <div className="text-sm text-content-secondary animate-pulse">
          Loading Personal OS...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-0">
      {/* Mobile Shell Wrapper */}
      <div className="flex h-screen w-full max-w-md flex-col border-x border-border-subtle bg-surface-0 shadow-2xl">
        {/* Header */}
        <header className="flex h-14 items-center justify-between border-b border-border-subtle bg-surface-1 px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-xs font-bold text-white">
              ❇
            </div>
            <div>
              <h1 className="text-xs font-bold text-content-primary">Personal OS</h1>
              <p className="text-[10px] text-emerald-400">● active</p>
            </div>
          </div>

          <button
            onClick={logout}
            className="rounded-md bg-surface-2 px-2.5 py-1 text-xs font-medium text-content-secondary hover:text-content-primary"
          >
            Logout
          </button>
        </header>

        {/* Main chat timeline */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <ChatTimeline
            messages={messages}
            onDoneItem={handleDoneItem}
            onRetry={handleRetry}
          />
          <div ref={scrollRef} />
        </div>

        {/* Input Composer */}
        <ChatComposer onSend={handleSendMessage} disabled={isSending} />
      </div>
    </main>
  );
}