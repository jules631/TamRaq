export interface Tenant {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface SalesforceConfigOut {
  loginUrl: string;
  clientId: string;
  integrationUsername: string;
}

export interface SalesforceConfigIn {
  loginUrl: string;
  clientId: string;
  integrationUsername: string;
  privateKeyPem: string;
}

export interface TestConnectionOut {
  orgId: string;
  instanceUrl: string;
  username: string;
}

export interface RecordType {
  id: string;
  name: string;
  developerName: string;
}

export interface LinkField {
  apiName: string;
  label: string;
}

export interface SyncConfigIn {
  householdAccountRecordTypeId: string | null;
  financialAccountHouseholdLookupFieldApiName: string | null;
  enablePositions: boolean;
}

export interface SyncConfigOut {
  householdAccountRecordTypeId: string | null;
  financialAccountHouseholdLookupFieldApiName: string | null;
  enablePositions: boolean;
}

export interface StartSyncOut {
  runId: string;
  sseToken: string;
}

export interface SyncRunListItem {
  id: string;
  status: "pending" | "running" | "success" | "partial" | "failed";
  startedAt: string;
  completedAt: string | null;
  totalRows: number;
  successCount: number;
  failureCount: number;
  duplicateCount: number;
}

export interface SyncRunOut extends SyncRunListItem {
  enablePositions: boolean;
  stageCounts: Record<string, Record<string, number>>;
  sanitizedErrors: Array<{
    stage: string;
    externalIdHash: string;
    message: string;
  }>;
}

// SSE event types
export type SseEvent =
  | { type: "stage"; stage: string; status: "started" | "done"; [k: string]: unknown }
  | { type: "progress"; stage: string; processed: number; total: number }
  | { type: "error"; stage: string; externalIdHash: string; message: string }
  | { type: "done"; status: string; successCount: number; failureCount: number; duplicateCount: number }
  | { type: "stream_end" };
