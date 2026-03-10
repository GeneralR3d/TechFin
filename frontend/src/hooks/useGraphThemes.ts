import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface GraphTheme {
  name: string;
  description: string;
  articleCount: number;
  avgSentiment: number | null;
}

async function themesFetcher(url: string): Promise<GraphTheme[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    name: (item.name as string) ?? "",
    description: (item.description as string) ?? "",
    articleCount: (item.article_count as number) ?? 0,
    avgSentiment: (item.avg_sentiment as number | null) ?? null,
  }));
}

export function useGraphThemes(limit = 15) {
  const { data, error, isLoading } = useSWR<GraphTheme[]>(
    `/api/graph/themes/active?limit=${limit}`,
    themesFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    themes: data ?? [],
    isLoading,
    error,
  };
}
