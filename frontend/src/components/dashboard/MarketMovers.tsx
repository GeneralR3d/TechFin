import { TrendingUp, TrendingDown, Flame } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketMovers, MoverStock } from "@/hooks/useMarketMovers";
import { cn } from "@/lib/utils";

function StockRow({ stock }: { stock: MoverStock }) {
  const isPositive = !stock.changePercentage.startsWith("-");
  return (
    <div className="flex items-center justify-between py-1">
      <div>
        <p className="font-semibold text-sm">{stock.ticker}</p>
        <p className="text-xs text-muted-foreground">{stock.volume} vol</p>
      </div>
      <div className="text-right">
        <p className="font-mono text-sm font-medium">${stock.price}</p>
        <p className={cn("text-xs font-medium", isPositive ? "text-green-500" : "text-red-500")}>
          {stock.changePercentage}
        </p>
      </div>
    </div>
  );
}

export function MarketMovers() {
  const { movers, isLoading, error } = useMarketMovers();

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (error || !movers) {
    return (
      <div className="text-muted-foreground text-sm py-4 text-center">
        Failed to load market movers.
      </div>
    );
  }

  return (
    <Accordion type="single" collapsible defaultValue="gainers" className="w-full">
      <AccordionItem value="gainers">
        <AccordionTrigger className="hover:no-underline">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <span className="font-medium text-green-500">Top Gainers</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col divide-y divide-border">
            {movers.topGainers.map((stock) => (
              <StockRow key={stock.ticker} stock={stock} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="losers">
        <AccordionTrigger className="hover:no-underline">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-red-500" />
            <span className="font-medium text-red-500">Top Losers</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col divide-y divide-border">
            {movers.topLosers.map((stock) => (
              <StockRow key={stock.ticker} stock={stock} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="active">
        <AccordionTrigger className="hover:no-underline">
          <div className="flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-500" />
            <span className="font-medium text-orange-500">Most Active</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col divide-y divide-border">
            {movers.mostActive.map((stock) => (
              <StockRow key={stock.ticker} stock={stock} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
