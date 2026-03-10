import { Building2, Factory, Globe, MapPin, User } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { getSentimentInfo } from "@/lib/sentiment-utils";
import type { EventEntities } from "@/hooks/useEventEntities";

interface EntitiesPanelProps {
  entities: EventEntities;
}

export function EntitiesPanel({ entities }: EntitiesPanelProps) {
  const navigate = useNavigate();

  const hasAny =
    entities.companies.length > 0 ||
    entities.geographies.length > 0 ||
    entities.institutions.length > 0 ||
    entities.persons.length > 0 ||
    entities.sectors.length > 0 ||
    entities.industries.length > 0;

  if (!hasAny) return null;

  return (
    <div className="mt-8 rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">Related Entities</h3>
      <div className="flex flex-wrap gap-6">
        {entities.companies.length > 0 && (
          <EntityGroup title="Companies" icon={<Building2 className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.companies.map((c) => (
                <Badge
                  key={c.ticker}
                  variant="secondary"
                  className={
                    "text-xs font-mono" +
                    (c.ticker.startsWith("__") ? "" : " cursor-pointer hover:bg-accent transition-colors")
                  }
                  onClick={
                    c.ticker.startsWith("__")
                      ? undefined
                      : () => navigate(`/entity/company/${encodeURIComponent(c.ticker)}`)
                  }
                >
                  {c.ticker}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}

        {entities.sectors.length > 0 && (
          <EntityGroup title="Sectors" icon={<Globe className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.sectors.map((s) => (
                <Badge
                  key={s}
                  variant="outline"
                  className="text-xs cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => navigate(`/entity/sector/${encodeURIComponent(s)}`)}
                >
                  {s}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}

        {entities.industries.length > 0 && (
          <EntityGroup title="Industries" icon={<Factory className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.industries.map((ind) => (
                <Badge
                  key={ind}
                  variant="outline"
                  className="text-xs cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => navigate(`/entity/industry/${encodeURIComponent(ind)}`)}
                >
                  {ind}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}

        {entities.geographies.length > 0 && (
          <EntityGroup title="Geographies" icon={<MapPin className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.geographies.map((g) => (
                <Badge
                  key={g.name}
                  variant="outline"
                  className="text-xs cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => navigate(`/entity/geography/${encodeURIComponent(g.name)}`)}
                >
                  {g.name}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}

        {entities.institutions.length > 0 && (
          <EntityGroup title="Institutions" icon={<Building2 className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.institutions.map((i) => (
                <Badge
                  key={i.name}
                  variant="outline"
                  className="text-xs cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => navigate(`/entity/institution/${encodeURIComponent(i.name)}`)}
                >
                  {i.name}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}

        {entities.persons.length > 0 && (
          <EntityGroup title="Persons" icon={<User className="h-3.5 w-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {entities.persons.map((p) => (
                <Badge
                  key={p.name}
                  variant="outline"
                  className="text-xs cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => navigate(`/entity/person/${encodeURIComponent(p.name)}`)}
                >
                  {p.name}
                  {p.role ? ` · ${p.role}` : ""}
                </Badge>
              ))}
            </div>
          </EntityGroup>
        )}
      </div>
    </div>
  );
}

function EntityGroup({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="min-w-0">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

interface TickerBadgeProps {
  ticker: string;
  sentiment: number | null;
}

export function TickerBadge({ ticker, sentiment }: TickerBadgeProps) {
  const info = sentiment !== null ? getSentimentInfo(sentiment) : null;
  return (
    <span
      className={
        "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-mono font-medium " +
        (info ? info.badgeClasses : "bg-secondary text-secondary-foreground")
      }
    >
      {ticker}
    </span>
  );
}
