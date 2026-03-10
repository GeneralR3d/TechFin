import { useGraphThemes } from "@/hooks/useGraphThemes";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

function ThemeSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 rounded-lg" />
      ))}
    </div>
  );
}

export function GraphThemesPanel() {
  const { themes, isLoading, error } = useGraphThemes(10);

  if (isLoading) return <ThemeSkeleton />;

  if (error || themes.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {error ? "Failed to load themes." : "No themes yet — ingest articles to populate graph."}
      </p>
    );
  }

  const maxCount = Math.max(...themes.map((t) => t.articleCount), 1);

  return (
    <div className="space-y-2">
      {themes.map((theme) => {
        const sentiment = theme.avgSentiment !== null
          ? getSentimentInfo(theme.avgSentiment)
          : null;
        const barWidth = Math.round((theme.articleCount / maxCount) * 100);

        return (
          <div
            key={theme.name}
            className="rounded-lg border border-border bg-card p-3 hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <p className="text-sm font-medium leading-snug line-clamp-1">
                {theme.name}
              </p>
              {sentiment && (
                <Badge className={sentiment.badgeClasses + " text-xs shrink-0"}>
                  {sentiment.label}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary/60 transition-all"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                {theme.articleCount}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
