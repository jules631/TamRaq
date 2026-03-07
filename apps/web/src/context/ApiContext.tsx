import React, { createContext, useContext, useMemo } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { createApiClient, type ApiClient } from "../api/client";
import { auth0Config } from "../auth/auth0";

const ApiContext = createContext<ApiClient | null>(null);

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const { getAccessTokenSilently } = useAuth0();

  const api = useMemo(
    () =>
      createApiClient(() =>
        getAccessTokenSilently({
          authorizationParams: { audience: auth0Config.audience },
        })
      ),
    [getAccessTokenSilently]
  );

  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}

export function useApi(): ApiClient {
  const ctx = useContext(ApiContext);
  if (!ctx) throw new Error("useApi must be used within ApiProvider");
  return ctx;
}
