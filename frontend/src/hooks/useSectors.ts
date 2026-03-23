import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface SectorData {
  symbol: string;
  name: string;
  weekReturn: number;
  ytdReturn: number;
  marketWeight: number;
  price: number;
}

async function sectorsFetcher(url: string): Promise<SectorData[]> {
  const data = await authedFetcher(url);
  return (data as Record<string, unknown>[]).map((item) => ({
    symbol: (item.symbol as string) ?? "",
    name: (item.name as string) ?? "",
    weekReturn: (item.week_return as number) ?? 0,
    ytdReturn: (item.ytd_return as number) ?? 0,
    marketWeight: (item.market_weight as number) ?? 0,
    price: (item.price as number) ?? 0,
  }));
}

export function useSectors() {
  const { data, error, isLoading } = useSWR<SectorData[]>(
    "/api/sectors",
    sectorsFetcher,
    { revalidateOnFocus: false, dedupingInterval: 60_000 }
  );

  return {
    sectors: data ?? [],
    isLoading,
    error,
  };
}
