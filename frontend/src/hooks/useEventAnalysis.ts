import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface AnalysisCitation {
  news_id: string;
  title: string;
  url: string;
}

export interface RelevantParty {
  name: string;
  role: string;
  significance: string;
}

export interface EventAnalysis {
  executive_summary: string;
  key_risks: string[];
  potential_developments: string[];
  relevant_parties: RelevantParty[];
  market_impact: string;
  citations: AnalysisCitation[];
}

async function analysisFetcher(url: string): Promise<EventAnalysis | null> {
  const data = await authedFetcher(url);
  if (!data) return null;
  return data as EventAnalysis;
}

export function useEventAnalysis(eventId: string | null) {
  const { data, error, isLoading } = useSWR<EventAnalysis | null>(
    eventId ? `/api/graph/events/${encodeURIComponent(eventId)}/analysis` : null,
    analysisFetcher,
    { revalidateOnFocus: false, dedupingInterval: 3_600_000 }
  );

  return {
    analysis: data ?? null,
    isLoading,
    error,
  };
}
