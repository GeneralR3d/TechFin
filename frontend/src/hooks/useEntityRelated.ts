import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";
import type { EventEntities } from "@/hooks/useEventEntities";

const EMPTY_ENTITIES: EventEntities = {
  companies: [], geographies: [], institutions: [], persons: [], sectors: [], industries: [],
};

async function entityRelatedFetcher(url: string): Promise<EventEntities> {
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

export function useEntityRelated(entityType: string | null, entityName: string | null) {
  const key =
    entityType && entityName
      ? `/api/graph/entity/${entityType}/${encodeURIComponent(entityName)}/related`
      : null;

  const { data, error, isLoading } = useSWR<EventEntities>(
    key,
    entityRelatedFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    entities: data ?? EMPTY_ENTITIES,
    isLoading,
    error,
  };
}
