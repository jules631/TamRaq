import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  Paper,
  Switch,
  Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { useApi } from "../context/ApiContext";
import { useTenant } from "../context/TenantContext";
import { useSyncRunning } from "../context/SyncRunningContext";
import StageStepper, { type StageInfo, type StageStatus } from "../components/StageStepper";
import ErrorTable, { type ErrorEntry } from "../components/ErrorTable";
import StatusChip from "../components/StatusChip";
import type { SseEvent } from "../api/types";

const STAGE_LABELS: Record<string, string> = {
  parse_and_validate: "Parse & Validate",
  upsert_households: "Upsert Households",
  upsert_contacts: "Upsert Contacts",
  resolve_ids: "Resolve IDs",
  upsert_acr: "Account-Contact Relations",
  upsert_financial_accounts: "Upsert Financial Accounts",
  upsert_positions: "Upsert Positions",
};

const STAGE_ORDER = Object.keys(STAGE_LABELS);

function buildInitialStages(enablePositions: boolean): StageInfo[] {
  return STAGE_ORDER.filter(
    (id) => enablePositions || id !== "upsert_positions"
  ).map((id) => ({ id, label: STAGE_LABELS[id], status: "pending" as StageStatus }));
}

type RunPhase = "idle" | "uploading" | "streaming" | "done";

export default function RunSync() {
  const api = useApi();
  const { selectedTenant } = useTenant();
  const { setSyncRunning } = useSyncRunning();
  const tenantId = selectedTenant?.id ?? "";

  const [file, setFile] = useState<File | null>(null);
  const [enablePositions, setEnablePositions] = useState(true);
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [stages, setStages] = useState<StageInfo[]>(buildInitialStages(true));
  const [errors, setErrors] = useState<ErrorEntry[]>([]);
  const [finalStatus, setFinalStatus] = useState<string | null>(null);
  const [counts, setCounts] = useState({ success: 0, failure: 0, duplicate: 0 });
  const [uploadError, setUploadError] = useState<string | null>(null);

  const esRef = useRef<EventSource | null>(null);
  const isRunning = phase === "uploading" || phase === "streaming";

  // Keep global running state in sync
  useEffect(() => {
    setSyncRunning(isRunning);
    return () => setSyncRunning(false);
  }, [isRunning, setSyncRunning]);

  // Prevent nav during run
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isRunning) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isRunning]);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => esRef.current?.close();
  }, []);

  const updateStage = useCallback((stageId: string, status: StageStatus, detail?: string) => {
    setStages((prev) =>
      prev.map((s) => (s.id === stageId ? { ...s, status, detail } : s))
    );
  }, []);

  const handleEvent = useCallback(
    (event: SseEvent) => {
      if (event.type === "stage") {
        updateStage(
          event.stage,
          event.status === "started" ? "started" : "done",
          event.status === "done" && "processed" in event
            ? `Processed: ${event.processed}`
            : undefined
        );
      } else if (event.type === "error") {
        setErrors((prev) => [...prev, event]);
        updateStage(event.stage, "error");
      } else if (event.type === "done") {
        setFinalStatus(event.status);
        setCounts({
          success: event.successCount,
          failure: event.failureCount,
          duplicate: event.duplicateCount,
        });
        setPhase("done");
        esRef.current?.close();
      }
      // stream_end is handled by onmessage returning
    },
    [updateStage]
  );

  const startRun = async () => {
    if (!tenantId || !file) return;
    setUploadError(null);
    setErrors([]);
    setFinalStatus(null);
    setStages(buildInitialStages(enablePositions));
    setCounts({ success: 0, failure: 0, duplicate: 0 });
    setPhase("uploading");

    try {
      const csvText = await file.text();
      const { runId, sseToken } = await api.startSync(tenantId, csvText, enablePositions);

      setPhase("streaming");
      const url = api.buildSseUrl(tenantId, runId, sseToken);
      const es = new EventSource(url);
      esRef.current = es;

      es.onmessage = (e) => {
        if (e.data === "[DONE]") {
          es.close();
          return;
        }
        try {
          const event: SseEvent = JSON.parse(e.data);
          if (event.type === "stream_end") {
            es.close();
          } else {
            handleEvent(event);
          }
        } catch {}
      };

      es.onerror = () => {
        es.close();
        setPhase("done");
      };
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to start sync");
      setPhase("idle");
    }
  };

  if (!tenantId) return <Typography>No tenant selected.</Typography>;

  return (
    <Box maxWidth={700}>
      <Typography variant="h5" gutterBottom>
        Run Sync
      </Typography>

      {/* Upload form */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Upload CSV
        </Typography>
        <Button
          variant="outlined"
          component="label"
          startIcon={<UploadFileIcon />}
          disabled={isRunning}
        >
          {file ? file.name : "Choose CSV file"}
          <input
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </Button>

        <FormControlLabel
          sx={{ display: "block", mt: 2 }}
          control={
            <Switch
              checked={enablePositions}
              disabled={isRunning}
              onChange={(e) => setEnablePositions(e.target.checked)}
            />
          }
          label="Sync Positions"
        />

        {uploadError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {uploadError}
          </Alert>
        )}

        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            onClick={startRun}
            disabled={!file || isRunning}
            startIcon={isRunning ? <CircularProgress size={18} color="inherit" /> : undefined}
          >
            {phase === "uploading"
              ? "Uploading…"
              : phase === "streaming"
              ? "Syncing…"
              : "Start Sync"}
          </Button>
        </Box>
      </Paper>

      {/* Progress */}
      {(phase === "streaming" || phase === "done") && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
            <Typography variant="subtitle1">Progress</Typography>
            {finalStatus && <StatusChip status={finalStatus} />}
          </Box>

          {phase === "done" && finalStatus && (
            <Box sx={{ display: "flex", gap: 2, mb: 2, flexWrap: "wrap" }}>
              <Chip label={`Success: ${counts.success}`} color="success" size="small" />
              <Chip label={`Failed: ${counts.failure}`} color={counts.failure > 0 ? "error" : "default"} size="small" />
              <Chip label={`Duplicates: ${counts.duplicate}`} size="small" />
            </Box>
          )}

          <StageStepper stages={stages} />
          <ErrorTable errors={errors} />
        </Paper>
      )}
    </Box>
  );
}
