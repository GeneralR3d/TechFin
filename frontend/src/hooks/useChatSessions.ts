import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";
import { getToken } from "@/lib/auth";

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export function useChatSessions() {
  const { data, error, isLoading, mutate } = useSWR<ChatSession[]>(
    "/api/ai/sessions",
    authedFetcher
  );

  const createSession = async (): Promise<ChatSession> => {
    const res = await fetch("/api/ai/sessions", {
      method: "POST",
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error("Failed to create session");
    const session: ChatSession = await res.json();
    await mutate();
    return session;
  };

  const deleteSession = async (id: string) => {
    const optimistic = (data ?? []).filter((s) => s.id !== id);
    await mutate(
      async () => {
        const res = await fetch(`/api/ai/sessions/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${getToken()}` },
        });
        if (!res.ok) throw new Error("Failed to delete session");
        return mutate();
      },
      { optimisticData: optimistic, rollbackOnError: true }
    );
  };

  return {
    sessions: data ?? [],
    isLoading,
    error,
    createSession,
    deleteSession,
    mutate,
  };
}
