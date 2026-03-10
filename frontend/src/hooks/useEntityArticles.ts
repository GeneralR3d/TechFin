import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";
import type { GraphArticle } from "@/hooks/useGraphNews";

async function entityArticlesFetcher(url: string): Promise<GraphArticle[]> {
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

export function useEntityArticles(entityType: string | null, entityName: string | null) {
  const key =
    entityType && entityName
      ? `/api/graph/entity/${entityType}/${encodeURIComponent(entityName)}/articles?limit=30`
      : null;

  const { data, error, isLoading } = useSWR<GraphArticle[]>(
    key,
    entityArticlesFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    articles: data ?? [],
    isLoading,
    error,
  };
}
