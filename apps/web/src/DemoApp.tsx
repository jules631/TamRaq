/**
 * DemoApp — renders the full application without Auth0.
 *
 * Used when VITE_DEMO_MODE=true. The API receives a static "demo-token"
 * bearer token that the backend accepts in DEMO_MODE without contacting Auth0.
 * The backend startup seed pre-creates a demo tenant so the app has data
 * to work with immediately.
 */

import React, { useMemo } from "react";
import { createApiClient } from "./api/client";
import { ApiContext } from "./context/ApiContext";
import { TenantProvider } from "./context/TenantContext";
import { SyncRunningProvider } from "./context/SyncRunningContext";
import { AppRoutes } from "./App";

function DemoApiProvider({ children }: { children: React.ReactNode }) {
  const api = useMemo(() => createApiClient(async () => "demo-token"), []);
  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}

export default function DemoApp() {
  return (
    <DemoApiProvider>
      <TenantProvider>
        <SyncRunningProvider>
          <AppRoutes />
        </SyncRunningProvider>
      </TenantProvider>
    </DemoApiProvider>
  );
}
