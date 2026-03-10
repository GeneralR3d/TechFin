import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";
import type { EventAnalysis } from "@/hooks/useEventAnalysis";

async function themeAnalysisFetcher(url: string): Promise<EventAnalysis | null> {
  const data = await authedFetcher(url);
  if (!data) return null;
  return data as EventAnalysis;
}

export function useThemeAnalysis(themeName: string | null) {
  const { data, error, isLoading } = useSWR<EventAnalysis | null>(
    themeName ? `/api/graph/themes/${encodeURIComponent(themeName)}/analysis` : null,
    themeAnalysisFetcher,
    { revalidateOnFocus: false, dedupingInterval: 3_600_000 }
  );

  return {
    analysis: data ?? null,
    isLoading,
    error,
  };
}
