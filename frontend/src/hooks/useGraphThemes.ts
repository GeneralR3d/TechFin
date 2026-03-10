import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface TopTicker {
  ticker: string;
  sentiment: number | null;
  count: number;
}

export interface GraphTheme {
  name: string;
  description: string;
  articleCount: number;
  avgSentiment: number | null;
  topTickers: TopTicker[];
}

async function themesFetcher(url: string): Promise<GraphTheme[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    name: (item.name as string) ?? "",
    description: (item.description as string) ?? "",
    articleCount: (item.article_count as number) ?? 0,
    avgSentiment: (item.avg_sentiment as number | null) ?? null,
    topTickers: ((item.top_tickers as Record<string, unknown>[]) ?? []).map((t) => ({
      ticker: (t.ticker as string) ?? "",
      sentiment: (t.sentiment as number | null) ?? null,
      count: (t.count as number) ?? 0,
    })),
  }));
}

export function useGraphThemes(limit = 15, days = 7) {
  const { data, error, isLoading } = useSWR<GraphTheme[]>(
    `/api/graph/themes/active?limit=${limit}&days=${days}`,
    themesFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    themes: data ?? [],
    isLoading,
    error,
  };
}
