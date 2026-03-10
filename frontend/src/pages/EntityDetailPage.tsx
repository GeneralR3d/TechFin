import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Newspaper } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArticleList } from "@/components/events/ArticleList";
import { EntitiesPanel } from "@/components/events/EntitiesPanel";
import { useEntityArticles } from "@/hooks/useEntityArticles";
import { useEntityRelated } from "@/hooks/useEntityRelated";

const ENTITY_LABELS: Record<string, string> = {
  company: "Company",
  sector: "Sector",
  industry: "Industry",
  geography: "Geography",
  institution: "Institution",
  person: "Person",
};

export function EntityDetailPage() {
  const { entityType, entityName } = useParams<{ entityType: string; entityName: string }>();
  const navigate = useNavigate();

  const decodedName = entityName ? decodeURIComponent(entityName) : "";
  const { articles, isLoading: articlesLoading, error: articlesError } = useEntityArticles(
    entityType ?? null,
    decodedName || null
  );
  const { entities } = useEntityRelated(entityType ?? null, decodedName || null);

  const label = entityType ? (ENTITY_LABELS[entityType] ?? entityType) : "";

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
          {label && (
            <Badge variant="secondary" className="text-xs">
              {label}
            </Badge>
          )}
        </div>
        <h1 className="text-2xl font-bold tracking-tight">{decodedName}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Newspaper className="h-3.5 w-3.5" />
            {articlesLoading
              ? "Loading…"
              : `${articles.length} article${articles.length !== 1 ? "s" : ""}`}
          </span>
        </div>
      </div>

      {/* Articles (full width) */}
      <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        News Articles
      </h2>
      <ArticleList articles={articles} isLoading={articlesLoading} error={articlesError} />

      {/* Related entities */}
      <EntitiesPanel entities={entities} />
    </main>
  );
}
