import { useState } from "react";
import { VercelTabs } from "@/components/ui/vercel-tabs";
import { ArticleCard } from "@/components/ui/article-cards";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useGraphThemes } from "@/hooks/useGraphThemes";
import { useGraphEvents } from "@/hooks/useGraphEvents";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import { CalendarDays, Newspaper, Tag } from "lucide-react";

const TABS = [
  { id: "themes", label: "Macro Themes" },
  { id: "events", label: "Recent Events" },
];

function sentimentGradient(score: number | null): string {
  if (score === null) return "from-slate-700 to-slate-900";
  if (score <= -0.35) return "from-red-700 to-red-900";
  if (score <= -0.15) return "from-orange-600 to-orange-900";
  if (score < 0.15) return "from-slate-600 to-slate-800";
  if (score < 0.35) return "from-lime-700 to-emerald-800";
  return "from-emerald-600 to-teal-800";
}

function CardSkeleton() {
  return <Skeleton className="h-64 rounded-xl" />;
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="col-span-full flex flex-col items-center justify-center py-16 text-muted-foreground">
      <Newspaper className="h-10 w-10 mb-3 opacity-30" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

function ThemesGrid() {
  const { themes, isLoading, error } = useGraphThemes(15);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid grid-cols-1">
        <EmptyState message="Could not load macro themes. Is Neo4j running?" />
      </div>
    );
  }

  if (themes.length === 0) {
    return (
      <div className="grid grid-cols-1">
        <EmptyState message="No themes found. Ingest some articles to populate the graph." />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {themes.map((theme) => {
        const sentiment = theme.avgSentiment !== null
          ? getSentimentInfo(theme.avgSentiment)
          : null;

        return (
          <ArticleCard
            key={theme.name}
            category="Macro Theme"
            title={theme.name}
            meta={`${theme.articleCount} article${theme.articleCount !== 1 ? "s" : ""}`}
            gradient={sentimentGradient(theme.avgSentiment)}
            badge={
              sentiment ? (
                <Badge className={sentiment.badgeClasses + " text-xs"}>
                  {sentiment.label}
                </Badge>
              ) : undefined
            }
          />
        );
      })}
    </div>
  );
}

function EventsList() {
  const { events, isLoading, error } = useGraphEvents(14, 30);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return <EmptyState message="Could not load events. Is Neo4j running?" />;
  }

  if (events.length === 0) {
    return (
      <EmptyState message="No events found. Ingest some articles to populate the graph." />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {events.map((event) => (
        <div
          key={event.id}
          className="flex items-start gap-4 rounded-xl border border-border bg-card p-4 hover:bg-accent/50 transition-colors"
        >
          <div className="flex-shrink-0 mt-0.5 rounded-md bg-primary/10 p-2">
            <Tag className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold leading-snug line-clamp-2">
              {event.title}
            </p>
            {event.description && (
              <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                {event.description}
              </p>
            )}
            <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
              {event.type && (
                <span className="rounded-md bg-secondary px-2 py-0.5 font-medium">
                  {event.type}
                </span>
              )}
              {event.date && (
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" />
                  {event.date}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Newspaper className="h-3 w-3" />
                {event.articleCount} article{event.articleCount !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function EventsTabs() {
  const [activeTab, setActiveTab] = useState("themes");

  return (
    <div>
      <div className="mb-8 border-b border-border pb-1">
        <VercelTabs
          tabs={TABS}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </div>

      {activeTab === "themes" && <ThemesGrid />}
      {activeTab === "events" && <EventsList />}
    </div>
  );
}
