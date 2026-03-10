import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Newspaper } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import { useGraphNewsByTheme } from "@/hooks/useGraphNewsByTheme";
import { useThemeAnalysis } from "@/hooks/useThemeAnalysis";
import { useThemeEntities } from "@/hooks/useThemeEntities";
import { AnalysisPanel } from "@/components/events/AnalysisPanel";
import { ArticleList } from "@/components/events/ArticleList";
import { EntitiesPanel } from "@/components/events/EntitiesPanel";

export function ThemeDetailPage() {
  const { themeName } = useParams<{ themeName: string }>();
  const navigate = useNavigate();

  const decodedName = themeName ? decodeURIComponent(themeName) : null;

  const { articles, isLoading: articlesLoading, error: articlesError } = useGraphNewsByTheme(decodedName);
  const { analysis, isLoading: analysisLoading } = useThemeAnalysis(decodedName);
  const { entities } = useThemeEntities(decodedName);

  // Derive avg sentiment from articles
  const scores = articles.map((a) => a.sentimentScore).filter((s): s is number => s !== null);
  const avgSentiment = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
  const sentimentInfo = avgSentiment !== null ? getSentimentInfo(avgSentiment) : null;

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
          <Badge variant="secondary" className="text-xs">
            Macro Theme
          </Badge>
          {sentimentInfo && (
            <Badge className={sentimentInfo.badgeClasses + " text-xs"}>
              {sentimentInfo.label}
            </Badge>
          )}
        </div>
        <h1 className="text-2xl font-bold tracking-tight">{decodedName}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Newspaper className="h-3.5 w-3.5" />
            {articlesLoading ? "Loading…" : `${articles.length} article${articles.length !== 1 ? "s" : ""}`}
          </span>
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
