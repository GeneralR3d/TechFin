import useSWR from "swr";
import { authedFetcher } from "@/lib/fetcher";

export interface EntityCompany {
  ticker: string;
  name: string;
}

export interface EntityGeography {
  name: string;
  geo_type: string;
}

export interface EntityInstitution {
  name: string;
  inst_type: string;
}

export interface EntityPerson {
  name: string;
  role: string;
}

export interface EventEntities {
  companies: EntityCompany[];
  geographies: EntityGeography[];
  institutions: EntityInstitution[];
  persons: EntityPerson[];
  sectors: string[];
  industries: string[];
}

async function entitiesFetcher(url: string): Promise<EventEntities> {
  const data = await authedFetcher(url) as Record<string, unknown>;
  return {
    companies: (data.companies as EntityCompany[]) ?? [],
    geographies: (data.geographies as EntityGeography[]) ?? [],
    institutions: (data.institutions as EntityInstitution[]) ?? [],
    persons: (data.persons as EntityPerson[]) ?? [],
    sectors: (data.sectors as string[]) ?? [],
    industries: (data.industries as string[]) ?? [],
  };
}

const EMPTY_ENTITIES: EventEntities = {
  companies: [], geographies: [], institutions: [], persons: [], sectors: [], industries: [],
};

export function useEventEntities(eventId: string | null) {
  const { data, error, isLoading } = useSWR<EventEntities>(
    eventId ? `/api/graph/events/${encodeURIComponent(eventId)}/entities` : null,
    entitiesFetcher,
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );

  return {
    entities: data ?? EMPTY_ENTITIES,
    isLoading,
    error,
  };
}
