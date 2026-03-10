import { useNavigate, useParams, useLocation } from "react-router-dom";
import { ArrowLeft, CalendarDays, Newspaper, Tag } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import { useEventArticles } from "@/hooks/useEventArticles";
import { useEventAnalysis } from "@/hooks/useEventAnalysis";
import { useEventEntities } from "@/hooks/useEventEntities";
import { AnalysisPanel } from "@/components/events/AnalysisPanel";
import { ArticleList } from "@/components/events/ArticleList";
import { EntitiesPanel } from "@/components/events/EntitiesPanel";
import type { GraphEvent } from "@/hooks/useGraphEvents";

export function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  // Event metadata passed via navigation state (from events list click)
  const event = (location.state as { event?: GraphEvent } | null)?.event ?? null;

  const { articles, isLoading: articlesLoading, error: articlesError } = useEventArticles(eventId ?? null);
  const { analysis, isLoading: analysisLoading } = useEventAnalysis(eventId ?? null);
  const { entities } = useEventEntities(eventId ?? null);

  const sentimentInfo =
    event?.avgSentiment !== undefined && event.avgSentiment !== null
      ? getSentimentInfo(event.avgSentiment)
      : null;

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        className="mb-6 -ml-2 gap-2 text-muted-foreground hover:text-foreground"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>

      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {event?.type && (
            <Badge variant="secondary" className="text-xs">
              {event.type}
            </Badge>
          )}
          {sentimentInfo && (
            <Badge className={sentimentInfo.badgeClasses + " text-xs"}>
              {sentimentInfo.label}
            </Badge>
          )}
        </div>
        <h1 className="text-2xl font-bold tracking-tight">
          {event?.title ?? eventId}
        </h1>
        {event?.description && (
          <p className="mt-2 text-sm text-muted-foreground max-w-3xl">{event.description}</p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          {event?.date && (
            <span className="flex items-center gap-1">
              <CalendarDays className="h-3.5 w-3.5" />
              {event.date}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Newspaper className="h-3.5 w-3.5" />
            {articlesLoading ? "Loading…" : `${articles.length} article${articles.length !== 1 ? "s" : ""}`}
          </span>
          {event?.id && (
            <span className="flex items-center gap-1">
              <Tag className="h-3.5 w-3.5" />
              {event.id}
            </span>
          )}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Left: Articles (60%) */}
        <div className="lg:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            News Articles
          </h2>
          <ArticleList
            articles={articles}
            isLoading={articlesLoading}
            error={articlesError}
          />
        </div>

        {/* Right: AI Analysis (40%) */}
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            AI Analysis
          </h2>
          <AnalysisPanel analysis={analysis} isLoading={analysisLoading} />
        </div>
      </div>

      {/* Entities panel */}
      <EntitiesPanel entities={entities} />
    </main>
  );
}
