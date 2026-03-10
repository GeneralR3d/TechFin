import { ExternalLink, Newspaper } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import type { GraphArticle } from "@/hooks/useGraphNews";

function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function getDateLabel(iso: string): string {
  if (!iso) return "Unknown Date";
  try {
    const date = new Date(iso);
    const today = new Date();
    const diffDays = Math.floor(
      (today.setHours(0, 0, 0, 0) - date.setHours(0, 0, 0, 0)) / 86400000
    );
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return new Date(iso).toLocaleDateString(undefined, {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "Unknown Date";
  }
}

interface ArticleListProps {
  articles: GraphArticle[];
  isLoading: boolean;
  error: unknown;
}

export function ArticleList({ articles, isLoading, error }: ArticleListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card py-12 text-muted-foreground">
        <Newspaper className="mb-2 h-8 w-8 opacity-30" />
        <p className="text-sm">Could not load articles.</p>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card py-12 text-muted-foreground">
        <Newspaper className="mb-2 h-8 w-8 opacity-30" />
        <p className="text-sm">No articles found.</p>
      </div>
    );
  }

  // Group articles by date label
  const groups: { label: string; articles: GraphArticle[] }[] = [];
  for (const article of articles) {
    const label = getDateLabel(article.publishedAt ?? "");
    const last = groups[groups.length - 1];
    if (last && last.label === label) {
      last.articles.push(article);
    } else {
      groups.push({ label, articles: [article] });
    }
  }

  return (
    <div className="space-y-3">
      {groups.map((group) => (
        <div key={group.label}>
          <div className="sticky top-0 z-10 py-1 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-background/80 backdrop-blur-sm">
            {group.label}
          </div>
          <div className="space-y-3">
            {group.articles.map((article) => {
              const sentiment = article.sentimentScore !== null
                ? getSentimentInfo(article.sentimentScore)
                : null;

              return (
                <div
                  key={article.newsId}
                  className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium leading-snug line-clamp-2">{article.title}</p>
                    {article.summary && (
                      <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{article.summary}</p>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      {article.source && <span>{article.source}</span>}
                      {article.publishedAt && (
                        <>
                          <span>·</span>
                          <span>{formatDate(article.publishedAt)}</span>
                        </>
                      )}
                      {sentiment && (
                        <Badge className={sentiment.badgeClasses + " text-xs"}>
                          {sentiment.label}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 flex items-center gap-1 text-xs text-primary hover:underline mt-0.5"
                    >
                      Read
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
