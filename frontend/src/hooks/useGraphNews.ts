import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface GraphArticle {
  newsId: string;
  title: string;
  url: string;
  summary: string;
  publishedAt: string;
  source: string;
  platform: string;
  sentimentScore: number | null;
}

async function newsFetcher(url: string): Promise<GraphArticle[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    newsId: (item.news_id as string) ?? "",
    title: (item.title as string) ?? "",
    url: (item.url as string) ?? "",
    summary: (item.summary as string) ?? "",
    publishedAt: (item.published_at as string) ?? "",
    source: (item.source as string) ?? "",
    platform: (item.platform as string) ?? "",
    sentimentScore: (item.sentiment_score as number | null) ?? null,
  }));
}

export function useGraphNews(ticker: string | null) {
  const { data, error, isLoading } = useSWR<GraphArticle[]>(
    ticker ? `/api/graph/news/company/${ticker}` : null,
    newsFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    articles: data ?? [],
    isLoading,
    error,
  };
}
