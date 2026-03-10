import { PageWrapper } from "@/components/layout/PageWrapper";
import { MarketMovers } from "@/components/dashboard/MarketMovers";
import { SectorHeatmap } from "@/components/dashboard/SectorHeatmap";
import { GraphThemesPanel } from "@/components/dashboard/GraphThemesPanel";

export function DashboardPage() {
  return (
    <PageWrapper
      title="Dashboard"
      description="Real-time sector performance and market movers"
    >
      <div className="flex gap-6">
        <div className="w-[28%] shrink-0">
          <h2 className="mb-4 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Market Movers
          </h2>
          <MarketMovers />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="mb-4 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Sector Performance
          </h2>
          <SectorHeatmap />
        </div>
        <div className="w-[26%] shrink-0">
          <h2 className="mb-4 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Macro Themes
          </h2>
          <GraphThemesPanel />
        </div>
      </div>
    </PageWrapper>
  );
}
