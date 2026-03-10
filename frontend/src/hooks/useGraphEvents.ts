import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface GraphEvent {
  id: string;
  title: string;
  type: string;
  date: string;
  description: string;
  articleCount: number;
}

async function eventsFetcher(url: string): Promise<GraphEvent[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    id: (item.id as string) ?? "",
    title: (item.title as string) ?? "",
    type: (item.type as string) ?? "",
    date: (item.date as string) ?? "",
    description: (item.description as string) ?? "",
    articleCount: (item.article_count as number) ?? 0,
  }));
}

export function useGraphEvents(days = 7, limit = 20) {
  const { data, error, isLoading } = useSWR<GraphEvent[]>(
    `/api/graph/events/recent?days=${days}&limit=${limit}`,
    eventsFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    events: data ?? [],
    isLoading,
    error,
  };
}
