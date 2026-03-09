import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface MoverStock {
  ticker: string;
  price: string;
  changeAmount: string;
  changePercentage: string;
  volume: string;
}

export interface MarketMovers {
  topGainers: MoverStock[];
  topLosers: MoverStock[];
  mostActive: MoverStock[];
}

function parseMover(item: Record<string, unknown>): MoverStock {
  return {
    ticker: (item.ticker as string) ?? "",
    price: (item.price as string) ?? "0",
    changeAmount: (item.change_amount as string) ?? "0",
    changePercentage: (item.change_percentage as string) ?? "0%",
    volume: (item.volume as string) ?? "0",
  };
}

async function moversFetcher(url: string): Promise<MarketMovers> {
  const data = await authedFetcher(url) as Record<string, unknown>;
  return {
    topGainers: ((data.top_gainers as Record<string, unknown>[]) ?? []).map(parseMover),
    topLosers: ((data.top_losers as Record<string, unknown>[]) ?? []).map(parseMover),
    mostActive: ((data.most_active as Record<string, unknown>[]) ?? []).map(parseMover),
  };
}

export function useMarketMovers() {
  const { data, error, isLoading } = useSWR<MarketMovers>(
    "/api/market/movers",
    moversFetcher,
    { revalidateOnFocus: false, dedupingInterval: 60_000 }
  );

  return {
    movers: data,
    isLoading,
    error,
  };
}
