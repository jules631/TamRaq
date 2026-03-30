import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { Tenant } from "../api/types";
import { useApi } from "./ApiContext";

interface TenantContextValue {
  tenants: Tenant[];
  selectedTenant: Tenant | null;
  setSelectedTenant: (t: Tenant) => void;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

const TenantContext = createContext<TenantContextValue>({
  tenants: [],
  selectedTenant: null,
  setSelectedTenant: () => {},
  loading: false,
  error: null,
  reload: () => {},
});

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const api = useApi();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.getMyTenants();
      setTenants(list);
      if (list.length > 0 && !selectedTenant) {
        setSelectedTenant(list[0]);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load tenants");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <TenantContext.Provider
      value={{
        tenants,
        selectedTenant,
        setSelectedTenant,
        loading,
        error,
        reload: load,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
