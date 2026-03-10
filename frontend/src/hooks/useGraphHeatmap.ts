import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface HeatmapEntry {
  sector: string;
  articleCount: number;
  avgSentiment: number | null;
}

async function heatmapFetcher(url: string): Promise<HeatmapEntry[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    sector: (item.sector as string) ?? "",
    articleCount: (item.article_count as number) ?? 0,
    avgSentiment: (item.avg_sentiment as number | null) ?? null,
  }));
}

export function useGraphHeatmap() {
  const { data, error, isLoading } = useSWR<HeatmapEntry[]>(
    "/api/graph/heatmap",
    heatmapFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    heatmap: data ?? [],
    isLoading,
    error,
  };
}
