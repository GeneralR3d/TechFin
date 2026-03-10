import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessageSquare, Plus, Send, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { getToken } from "@/lib/auth";
import { useChatSessions } from "@/hooks/useChatSessions";
import { useChatMessages } from "@/hooks/useChatMessages";
import type { ChatMessage } from "@/hooks/useChatMessages";

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function ChatPage() {
  const { sessions, createSession, deleteSession, mutate: mutateSessions } = useChatSessions();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const { messages: dbMessages, mutate: mutateMessages } = useChatMessages(activeSessionId);

  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Abort any in-flight stream when the component unmounts (navigating away)
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // Sync local messages with DB messages when session changes
  useEffect(() => {
    setLocalMessages(dbMessages);
    setStreamingContent("");
  }, [activeSessionId, dbMessages]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, streamingContent]);

  const handleNewChat = async () => {
    const session = await createSession();
    setActiveSessionId(session.id);
    setLocalMessages([]);
    setStreamingContent("");
  };

  const handleSelectSession = (id: string) => {
    if (id === activeSessionId) return;
    setActiveSessionId(id);
    setStreamingContent("");
    setIsStreaming(false);
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    if (activeSessionId === id) {
      setActiveSessionId(null);
      setLocalMessages([]);
      setStreamingContent("");
    }
  };

  const handleSend = async () => {
    const message = input.trim();
    if (!message || isStreaming) return;

    setInput("");
    setIsStreaming(true);

    // Optimistically add user message
    const optimisticUser: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId ?? "",
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, optimisticUser]);
    setStreamingContent("");

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ message, session_id: activeSessionId }),
        signal: abortController.signal,
      });

      if (!res.ok) throw new Error(`Chat failed: ${res.status}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let accumulated = "";
      let resolvedSessionId = activeSessionId;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Parse [SESSION:uuid] prefix on first chunk
        if (chunk.startsWith("[SESSION:")) {
          const end = chunk.indexOf("]");
          if (end !== -1) {
            resolvedSessionId = chunk.slice(9, end);
            setActiveSessionId(resolvedSessionId);
            // Remaining text after \n is actual content
            const rest = chunk.slice(end + 2); // skip "]\n"
            if (rest) {
              accumulated = rest;
              setStreamingContent(rest);
            }
            continue;
          }
        }

        // Append token delta to accumulated content
        accumulated += chunk;
        setStreamingContent(accumulated);
      }

      // Finalize: add assistant message to local state
      const assistantMsg: ChatMessage = {
        id: `temp-asst-${Date.now()}`,
        session_id: resolvedSessionId ?? "",
        role: "assistant",
        content: accumulated,
        created_at: new Date().toISOString(),
      };
      setLocalMessages((prev) => [...prev, assistantMsg]);
      setStreamingContent("");

      // Revalidate
      if (resolvedSessionId) {
        await mutateMessages();
      }
      await mutateSessions();
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Chat error:", err);
      setStreamingContent("");
    } finally {
      abortControllerRef.current = null;
      setIsStreaming(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-border flex flex-col">
        <div className="p-3 border-b border-border">
          <Button
            onClick={handleNewChat}
            className="w-full gap-2"
            variant="default"
            size="sm"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-2 space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No conversations yet
              </p>
            )}
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
                className={cn(
                  "w-full text-left rounded-md px-3 py-2 text-sm transition-colors group flex items-start justify-between gap-2",
                  session.id === activeSessionId
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                )}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <MessageSquare className="h-3 w-3 shrink-0" />
                    <span className="truncate font-medium text-xs">
                      {session.title}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 ml-4">
                    {relativeTime(session.created_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-destructive shrink-0"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeSessionId == null ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto" />
              <div>
                <p className="font-medium">Start a conversation</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Ask about market events, themes, or companies in the graph.
                </p>
              </div>
              <Button onClick={handleNewChat} className="gap-2">
                <Plus className="h-4 w-4" />
                New Chat
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="max-w-2xl mx-auto space-y-4">
                {localMessages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {isStreaming && streamingContent && (
                  <StreamingBubble content={streamingContent} />
                )}
                {isStreaming && !streamingContent && (
                  <ThinkingBubble />
                )}
                <div ref={bottomRef} />
              </div>
            </div>

            <div className="border-t border-border p-4">
              <div className="max-w-2xl mx-auto flex gap-2 items-end">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about market events, themes, companies…"
                  className="resize-none min-h-[44px] max-h-32"
                  rows={1}
                  disabled={isStreaming}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isStreaming}
                  size="icon"
                  className="shrink-0"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Press Enter to send · Shift+Enter for new line
              </p>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-2xl rounded-tr-sm whitespace-pre-wrap"
            : "bg-muted text-foreground rounded-2xl rounded-tl-sm"
        )}
      >
        {isUser ? message.content : <MarkdownContent content={message.content} />}
      </div>
    </div>
  );
}

function StreamingBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] px-4 py-2.5 text-sm leading-relaxed bg-muted text-foreground rounded-2xl rounded-tl-sm">
        <MarkdownContent content={content} />
        <span className="inline-block w-0.5 h-3.5 bg-foreground/70 ml-0.5 animate-pulse align-middle" />
      </div>
    </div>
  );
}

function ThinkingBubble() {
  return (
    <div className="flex justify-start">
      <div className="px-4 py-3 bg-muted rounded-2xl rounded-tl-sm">
        <div className="flex gap-1 items-center">
          <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        h1: ({ children }) => (
          <h1 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-sm font-bold mb-2 mt-3 first:mt-0">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h3>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>
        ),
        li: ({ children }) => <li className="ml-2">{children}</li>,
        code: ({ children, className }) => {
          const isBlock = !!className?.includes("language-");
          return isBlock ? (
            <code className="block bg-background/50 rounded p-2 my-2 text-xs font-mono overflow-x-auto whitespace-pre">
              {children}
            </code>
          ) : (
            <code className="bg-background/50 rounded px-1 py-0.5 text-xs font-mono">
              {children}
            </code>
          );
        },
        pre: ({ children }) => <pre className="my-2">{children}</pre>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-muted-foreground/40 pl-3 my-2 text-muted-foreground italic">
            {children}
          </blockquote>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:opacity-80"
          >
            {children}
          </a>
        ),
        hr: () => <hr className="my-3 border-muted-foreground/20" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
