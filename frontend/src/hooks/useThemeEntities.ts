import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";
import type { EventEntities } from "@/hooks/useEventEntities";

async function themeEntitiesFetcher(url: string): Promise<EventEntities> {
  const data = await authedFetcher(url) as Record<string, unknown>;
  return {
    companies: (data.companies as EventEntities["companies"]) ?? [],
    geographies: (data.geographies as EventEntities["geographies"]) ?? [],
    institutions: (data.institutions as EventEntities["institutions"]) ?? [],
    persons: (data.persons as EventEntities["persons"]) ?? [],
    sectors: (data.sectors as string[]) ?? [],
    industries: (data.industries as string[]) ?? [],
  };
}

const EMPTY_ENTITIES: EventEntities = {
  companies: [], geographies: [], institutions: [], persons: [], sectors: [], industries: [],
};

export function useThemeEntities(themeName: string | null) {
  const { data, error, isLoading } = useSWR<EventEntities>(
    themeName ? `/api/graph/themes/${encodeURIComponent(themeName)}/entities` : null,
    themeEntitiesFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    entities: data ?? EMPTY_ENTITIES,
    isLoading,
    error,
  };
}
