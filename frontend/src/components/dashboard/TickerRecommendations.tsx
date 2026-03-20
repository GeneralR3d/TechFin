import { useState } from "react";
import useSWR from "swr";
import { PortfolioSuggestionsResponse, TickerSuggestion } from "@/types/ticker";
import { authedFetcher } from "@/lib/fetcher";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Lightbulb, TrendingUp, TrendingDown, Info, ExternalLink } from "lucide-react";

function fmt(pct: number | null): string {
  if (pct === null || pct === undefined) return "—";
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function PctBlock({ label, pct }: { label: string | null; pct: number | null }) {
  const isNeg = pct !== null && pct < 0;
  const isPos = pct !== null && pct > 0;
  return (
    <div className="flex flex-col items-center">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 text-center leading-tight">
        {label ?? "—"}
      </span>
      <span
        className={`text-xl font-bold tabular-nums ${
          isNeg ? "text-red-500" : isPos ? "text-emerald-500" : "text-muted-foreground"
        }`}
      >
        {fmt(pct)}
      </span>
    </div>
  );
}

function ActionPill({ action }: { action: TickerSuggestion["action"] }) {
  const isSell = action === "SELL";
  return (
    <div
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-bold ${
        isSell
          ? "bg-red-500/15 text-red-600 dark:text-red-400"
          : "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
      }`}
    >
      {isSell ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
      {action}
    </div>
  );
}

function ConfidencePip({ confidence }: { confidence: TickerSuggestion["confidence"] }) {
  const map = { low: 1, medium: 2, high: 3 };
  const filled = map[confidence] ?? 1;
  const colors = { low: "bg-orange-400", medium: "bg-yellow-400", high: "bg-emerald-400" };
  return (
    <span className="flex items-center gap-0.5" title={`${confidence} confidence`}>
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          className={`inline-block h-1.5 w-2 rounded-sm ${i <= filled ? colors[confidence] : "bg-muted"}`}
        />
      ))}
    </span>
  );
}

function SuggestionCard({ s, onClick }: { s: TickerSuggestion; onClick: () => void }) {
  return (
    <div
      className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3 min-w-0 cursor-pointer hover:border-primary/40 hover:bg-muted/30 transition-colors"
      onClick={onClick}
    >
      {/* Top: ticker + action */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <span className="font-mono text-base font-bold tracking-tight">{s.ticker}</span>
          <span className="text-[11px] text-muted-foreground">{s.quantity} shares</span>
          <ConfidencePip confidence={s.confidence} />
        </div>
        <ActionPill action={s.action} />
      </div>

      {/* Middle: percentage estimates */}
      <div className="flex items-center gap-4 rounded-lg bg-muted/40 px-4 py-2.5">
        <PctBlock label={s.short_term_label} pct={s.short_term_pct} />
        <div className="h-8 w-px bg-border" />
        <PctBlock label={s.long_term_label} pct={s.long_term_pct} />
      </div>

      {/* Bottom: price outlook */}
      {s.price_outlook && (
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">{s.price_outlook}</p>
      )}
    </div>
  );
}

function SuggestionModal({ s, open, onClose }: { s: TickerSuggestion; open: boolean; onClose: () => void }) {
  const isSell = s.action === "SELL";
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="font-mono text-lg font-bold">{s.ticker}</span>
              <ActionPill action={s.action} />
            </div>
            <span className="text-sm font-normal text-muted-foreground">{s.quantity} shares</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-5 pt-1">
          {/* Confidence */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground uppercase tracking-wide">Confidence</span>
            <ConfidencePip confidence={s.confidence} />
            <span className="text-xs text-muted-foreground capitalize">{s.confidence}</span>
          </div>

          {/* Price estimates */}
          <div className="flex items-center gap-6 rounded-xl bg-muted/40 px-6 py-4">
            <PctBlock label={s.short_term_label} pct={s.short_term_pct} />
            <div className="h-10 w-px bg-border" />
            <PctBlock label={s.long_term_label} pct={s.long_term_pct} />
          </div>

          {/* Price outlook */}
          {s.price_outlook && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">
                Price Outlook
              </h4>
              <p className="text-sm text-foreground leading-relaxed">{s.price_outlook}</p>
            </div>
          )}

          {/* AI Reasoning */}
          {s.reasoning && (
            <div className={`rounded-lg p-3.5 ${isSell ? "bg-red-500/8" : "bg-emerald-500/8"}`}>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">
                AI Reasoning
              </h4>
              <p className="text-sm leading-relaxed">{s.reasoning}</p>
            </div>
          )}

          {/* Citations */}
          {s.citations && s.citations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                Sources
              </h4>
              <ul className="flex flex-col gap-1.5">
                {s.citations.map((c, i) => (
                  <li key={i}>
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-2 rounded-md px-2 py-1.5 text-sm text-primary hover:bg-muted/50 transition-colors group"
                    >
                      <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-60 group-hover:opacity-100" />
                      <span className="leading-snug">{c.title || c.url}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function TickerRecommendations() {
  const { data, isLoading, error } = useSWR<PortfolioSuggestionsResponse>(
    "/api/suggestions",
    authedFetcher
  );
  const [selected, setSelected] = useState<TickerSuggestion | null>(null);

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Lightbulb className="h-4 w-4 text-amber-500" />
            AI Portfolio Suggestions
            <span className="ml-auto text-xs font-normal text-muted-foreground">
              Short-term price outlook · click a card for details
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-44 w-full rounded-xl" />
              ))}
            </div>
          ) : error ? (
            <p className="text-sm text-muted-foreground">Failed to load suggestions.</p>
          ) : !data || data.suggestions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Add holdings in Settings to receive AI-powered hold/sell recommendations.
            </p>
          ) : (
            <div className="space-y-3">
              {/* Market context banner */}
              {data.market_context && (
                <div className="flex gap-2 rounded-lg bg-muted/50 px-3 py-2.5 text-xs text-muted-foreground">
                  <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary/70" />
                  <span className="leading-relaxed">{data.market_context}</span>
                </div>
              )}
              {/* Responsive grid — one card per ticker */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {data.suggestions.map((s) => (
                  <SuggestionCard key={s.ticker} s={s} onClick={() => setSelected(s)} />
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {selected && (
        <SuggestionModal
          s={selected}
          open={true}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
