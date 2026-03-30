import type {
  LinkField,
  RecordType,
  SalesforceConfigIn,
  SalesforceConfigOut,
  StartSyncOut,
  SyncConfigIn,
  SyncConfigOut,
  SyncRunListItem,
  SyncRunOut,
  Tenant,
  TestConnectionOut,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };
  if (!(options.body instanceof FormData) && options.method !== "GET" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const err = await resp.json();
      detail = err.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export function createApiClient(getToken: () => Promise<string>) {
  const tok = () => getToken();

  return {
    // Tenants
    getMyTenants: () => tok().then((t) => request<Tenant[]>("/api/me/tenants", t)),

    // Salesforce config
    getSalesforceConfig: (tenantId: string) =>
      tok().then((t) =>
        request<SalesforceConfigOut>(`/api/tenants/${tenantId}/config/salesforce`, t)
      ),
    putSalesforceConfig: (tenantId: string, body: SalesforceConfigIn) =>
      tok().then((t) =>
        request<{ status: string }>(`/api/tenants/${tenantId}/config/salesforce`, t, {
          method: "PUT",
          body: JSON.stringify(body),
        })
      ),

    // Sync config
    getSyncConfig: (tenantId: string) =>
      tok().then((t) =>
        request<SyncConfigOut>(`/api/tenants/${tenantId}/config/sync`, t)
      ),
    putSyncConfig: (tenantId: string, body: SyncConfigIn) =>
      tok().then((t) =>
        request<{ status: string }>(`/api/tenants/${tenantId}/config/sync`, t, {
          method: "PUT",
          body: JSON.stringify(body),
        })
      ),

    // Test connection
    testConnection: (tenantId: string) =>
      tok().then((t) =>
        request<TestConnectionOut>(
          `/api/tenants/${tenantId}/salesforce/test`,
          t,
          { method: "POST" }
        )
      ),

    // Discovery
    getAccountRecordTypes: (tenantId: string) =>
      tok().then((t) =>
        request<RecordType[]>(
          `/api/tenants/${tenantId}/salesforce/account-record-types`,
          t
        )
      ),
    getLinkFields: (tenantId: string) =>
      tok().then((t) =>
        request<LinkField[]>(
          `/api/tenants/${tenantId}/salesforce/financialaccount-household-link-fields`,
          t
        )
      ),

    // Sync run
    startSync: (tenantId: string, csvText: string, enablePositions: boolean) =>
      tok().then((t) =>
        request<StartSyncOut>(
          `/api/tenants/${tenantId}/sync/run?enable_positions=${enablePositions}`,
          t,
          {
            method: "POST",
            headers: { "Content-Type": "text/csv" },
            body: csvText,
          }
        )
      ),

    listSyncRuns: (tenantId: string, limit = 50) =>
      tok().then((t) =>
        request<SyncRunListItem[]>(
          `/api/tenants/${tenantId}/sync/runs?limit=${limit}`,
          t
        )
      ),

    getSyncRun: (tenantId: string, runId: string) =>
      tok().then((t) =>
        request<SyncRunOut>(`/api/tenants/${tenantId}/sync/runs/${runId}`, t)
      ),

    // SSE token is in the StartSyncOut; EventSource URL is built here
    buildSseUrl: (tenantId: string, runId: string, sseToken: string) =>
      `${API_BASE}/api/tenants/${tenantId}/sync/runs/${runId}/events?token=${encodeURIComponent(sseToken)}`,
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
