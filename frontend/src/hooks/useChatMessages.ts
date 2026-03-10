import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSessionDetail {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export function useChatMessages(sessionId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<ChatSessionDetail>(
    sessionId ? `/api/ai/sessions/${sessionId}` : null,
    authedFetcher
  );

  return {
    session: data ?? null,
    messages: data?.messages ?? [],
    isLoading,
    error,
    mutate,
  };
}
