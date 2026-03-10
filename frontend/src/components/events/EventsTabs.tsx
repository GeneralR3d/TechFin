import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { VercelTabs } from "@/components/ui/vercel-tabs";
import { ArticleCard } from "@/components/ui/article-cards";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useGraphThemes } from "@/hooks/useGraphThemes";
import { useGraphEvents } from "@/hooks/useGraphEvents";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import { TickerBadge } from "@/components/events/EntitiesPanel";
import { CalendarDays, Newspaper, Search, Tag } from "lucide-react";

const TABS = [
  { id: "themes", label: "Macro Themes" },
  { id: "events", label: "Recent Events" },
];

const TIME_OPTIONS = [
  { label: "24H", days: 1 },
  { label: "7D", days: 7 },
  { label: "30D", days: 30 },
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

function ThemesGrid({ search, days }: { search: string; days: number }) {
  const navigate = useNavigate();
  const { themes, isLoading, error } = useGraphThemes(15, days);

  const filtered = search.trim()
    ? themes.filter((t) =>
        t.name.toLowerCase().includes(search.toLowerCase()) ||
        (t.description ?? "").toLowerCase().includes(search.toLowerCase())
      )
    : themes;

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

  if (filtered.length === 0) {
    return (
      <div className="grid grid-cols-1">
        <EmptyState message={search ? "No themes match your search." : "No themes found. Ingest some articles to populate the graph."} />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {filtered.map((theme) => {
        const sentiment = theme.avgSentiment !== null
          ? getSentimentInfo(theme.avgSentiment)
          : null;

        return (
          <div
            key={theme.name}
            className="cursor-pointer"
            onClick={() => navigate(`/theme/${encodeURIComponent(theme.name)}`)}
          >
            <ArticleCard
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
              footer={
                theme.topTickers.length > 0 ? (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {theme.topTickers.map((t) => (
                      <TickerBadge key={t.ticker} ticker={t.ticker} sentiment={t.sentiment} />
                    ))}
                  </div>
                ) : undefined
              }
            />
          </div>
        );
      })}
    </div>
  );
}

function EventsList({ days, search }: { days: number; search: string }) {
  const navigate = useNavigate();
  const { events, isLoading, error } = useGraphEvents(days, 30);

  const filtered = search.trim()
    ? events.filter((e) =>
        e.title.toLowerCase().includes(search.toLowerCase()) ||
        (e.description ?? "").toLowerCase().includes(search.toLowerCase())
      )
    : events;

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

  if (filtered.length === 0) {
    return (
      <EmptyState message={search ? "No events match your search." : "No events found. Ingest some articles to populate the graph."} />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {filtered.map((event) => {
        const sentiment = event.avgSentiment !== null
          ? getSentimentInfo(event.avgSentiment)
          : null;

        return (
          <div
            key={event.id}
            className="flex items-start gap-4 rounded-xl border border-border bg-card p-4 hover:bg-accent/50 transition-colors cursor-pointer"
            onClick={() => navigate(`/event/${encodeURIComponent(event.id)}`, { state: { event } })}
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
              <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
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
                {sentiment && (
                  <Badge className={sentiment.badgeClasses + " text-xs"}>
                    {sentiment.label}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function EventsTabs() {
  const [activeTab, setActiveTab] = useState("themes");
  const [search, setSearch] = useState("");
  const [days, setDays] = useState(7);

  return (
    <div>
      {/* Search bar */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          className="pl-9"
          placeholder="Search themes and events…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="border-b border-border pb-1 flex-1">
          <VercelTabs
            tabs={TABS}
            activeTab={activeTab}
            onTabChange={(tab) => { setActiveTab(tab); setSearch(""); }}
          />
        </div>

        {/* Time toggle */}
        <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 shrink-0">
          {TIME_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              onClick={() => setDays(opt.days)}
              className={
                "rounded-md px-3 py-1 text-xs font-medium transition-colors " +
                (days === opt.days
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "themes" && <ThemesGrid search={search} days={days} />}
      {activeTab === "events" && <EventsList days={days} search={search} />}
    </div>
  );
}
