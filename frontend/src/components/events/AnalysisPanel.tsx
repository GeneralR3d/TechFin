import { AlertTriangle, BookOpen, ExternalLink, Lightbulb, TrendingUp, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { EventAnalysis } from "@/hooks/useEventAnalysis";

interface AnalysisPanelProps {
  analysis: EventAnalysis | null;
  isLoading: boolean;
}

export function AnalysisPanel({ analysis, isLoading }: AnalysisPanelProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-5 w-28" />
        <Skeleton className="h-20 w-full rounded-xl" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card p-8 text-center text-muted-foreground">
        <BookOpen className="mb-3 h-8 w-8 opacity-30" />
        <p className="text-sm font-medium">Analysis unavailable</p>
        <p className="mt-1 text-xs">No OpenAI API key configured or no articles to analyze.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {analysis.executive_summary && (
        <Section icon={<BookOpen className="h-4 w-4" />} title="Executive Summary">
          <p className="text-sm text-foreground leading-relaxed">{analysis.executive_summary}</p>
        </Section>
      )}

      {analysis.market_impact && (
        <Section icon={<TrendingUp className="h-4 w-4" />} title="Market Impact">
          <p className="text-sm text-foreground leading-relaxed">{analysis.market_impact}</p>
        </Section>
      )}

      {analysis.key_risks && analysis.key_risks.length > 0 && (
        <Section icon={<AlertTriangle className="h-4 w-4" />} title="Key Risks">
          <ul className="space-y-1.5">
            {analysis.key_risks.map((risk, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
                {risk}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {analysis.potential_developments && analysis.potential_developments.length > 0 && (
        <Section icon={<Lightbulb className="h-4 w-4" />} title="Potential Developments">
          <ul className="space-y-1.5">
            {analysis.potential_developments.map((dev, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                {dev}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {analysis.relevant_parties && analysis.relevant_parties.length > 0 && (
        <Section icon={<Users className="h-4 w-4" />} title="Relevant Parties">
          <div className="space-y-2">
            {analysis.relevant_parties.map((party, i) => (
              <div key={i} className="rounded-lg border border-border bg-background p-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{party.name}</span>
                  {party.role && (
                    <Badge variant="secondary" className="text-xs">
                      {party.role}
                    </Badge>
                  )}
                </div>
                {party.significance && (
                  <p className="mt-1 text-xs text-muted-foreground">{party.significance}</p>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {analysis.citations && analysis.citations.length > 0 && (
        <Section icon={<ExternalLink className="h-4 w-4" />} title="Citations">
          <ul className="space-y-1.5">
            {analysis.citations.map((cite, i) => (
              <li key={i} className="text-xs">
                {cite.url ? (
                  <a
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline line-clamp-1"
                  >
                    {cite.title || cite.url}
                  </a>
                ) : (
                  <span className="text-muted-foreground line-clamp-1">{cite.title}</span>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
        <span className="text-muted-foreground">{icon}</span>
        {title}
      </div>
      {children}
    </div>
  );
}
