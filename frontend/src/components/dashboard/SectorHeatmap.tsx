import { Treemap, ResponsiveContainer, Tooltip } from "recharts";
import { useSectors, SectorData } from "@/hooks/useSectors";
import { Skeleton } from "@/components/ui/skeleton";

function getColor(dayReturn: number): string {
  if (dayReturn < -2) return "#dc2626";
  if (dayReturn < -0.5) return "#f87171";
  if (dayReturn < 0.5) return "#6b7280";
  if (dayReturn < 2) return "#4ade80";
  return "#16a34a";
}

interface TreemapNode {
  name: string;
  symbol: string;
  dayReturn: number;
  ytdReturn: number;
  marketWeight: number;
  price: number;
  size: number;
  [key: string]: unknown;
}

interface CustomContentProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  dayReturn?: number;
}

function CustomContent({ x = 0, y = 0, width = 0, height = 0, name = "", dayReturn = 0 }: CustomContentProps) {
  const color = getColor(dayReturn);
  const showText = width > 50 && height > 40;

  return (
    <g>
      <rect
        x={x + 1}
        y={y + 1}
        width={width - 2}
        height={height - 2}
        style={{ fill: color, stroke: "hsl(var(--background))", strokeWidth: 2, opacity: 0.9 }}
        rx={4}
      />
      {showText && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 8}
            textAnchor="middle"
            fill="white"
            fontSize={Math.min(13, width / 7)}
            fontWeight="600"
          >
            {name.length > 12 ? name.slice(0, 10) + "…" : name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill="white"
            fontSize={Math.min(12, width / 8)}
            fontWeight="500"
          >
            {dayReturn >= 0 ? "+" : ""}{dayReturn.toFixed(2)}%
          </text>
        </>
      )}
    </g>
  );
}

interface TooltipPayload {
  payload?: TreemapNode;
}

function CustomTooltip({ payload }: { payload?: TooltipPayload[] }) {
  if (!payload?.length || !payload[0]?.payload) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-popover border border-border rounded-md px-3 py-2 shadow-md text-sm">
      <p className="font-semibold mb-1">{d.name} ({d.symbol})</p>
      <p>Day Return: <span className={d.dayReturn >= 0 ? "text-green-500" : "text-red-500"}>
        {d.dayReturn >= 0 ? "+" : ""}{d.dayReturn.toFixed(2)}%
      </span></p>
      <p className="text-muted-foreground">Market Weight: {d.marketWeight.toFixed(1)}%</p>
      <p className="text-muted-foreground">YTD Return: {d.ytdReturn >= 0 ? "+" : ""}{d.ytdReturn.toFixed(2)}%</p>
      <p className="text-muted-foreground">Price: ${d.price.toFixed(2)}</p>
    </div>
  );
}

export function SectorHeatmap() {
  const { sectors, isLoading, error } = useSectors();

  if (isLoading) {
    return <Skeleton className="h-[400px] w-full rounded-lg" />;
  }

  if (error) {
    return (
      <div className="h-[400px] flex items-center justify-center text-muted-foreground text-sm">
        Failed to load sector data.
      </div>
    );
  }

  const data: TreemapNode[] = sectors.map((s: SectorData) => ({
    name: s.name,
    symbol: s.symbol,
    dayReturn: s.dayReturn,
    ytdReturn: s.ytdReturn,
    marketWeight: s.marketWeight,
    price: s.price,
    size: s.marketWeight,
  }));

  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          aspectRatio={4 / 3}
          content={(props) => (
            <CustomContent
              {...props}
              dayReturn={(props as unknown as { dayReturn?: number }).dayReturn}
            />
          )}
        >
          <Tooltip content={<CustomTooltip />} />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
}
