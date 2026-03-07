import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Typography,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../context/ApiContext";
import { useTenant } from "../context/TenantContext";
import StatusChip from "../components/StatusChip";
import ErrorTable from "../components/ErrorTable";
import StageStepper, { type StageInfo } from "../components/StageStepper";
import type { SyncRunOut } from "../api/types";

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

function buildStagesFromRun(run: SyncRunOut): StageInfo[] {
  const isDone = run.status !== "running" && run.status !== "pending";
  return STAGE_ORDER.filter(
    (id) => run.enablePositions || id !== "upsert_positions"
  ).map((id) => {
    const counts = run.stageCounts[id];
    const detail = counts
      ? Object.entries(counts)
          .map(([k, v]) => `${k}: ${v}`)
          .join(", ")
      : undefined;
    const hasErrors = run.sanitizedErrors.some((e) => e.stage === id);
    const status = !isDone
      ? "pending"
      : counts
      ? hasErrors
        ? "error"
        : "done"
      : "pending";
    return { id, label: STAGE_LABELS[id], status, detail };
  });
}

function fmtDate(dt: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

export default function SyncRunDetails() {
  const api = useApi();
  const { selectedTenant } = useTenant();
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const tenantId = selectedTenant?.id ?? "";

  const [run, setRun] = useState<SyncRunOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId || !runId) return;
    setLoading(true);
    api
      .getSyncRun(tenantId, runId)
      .then((r) => setRun(r))
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Failed to load run")
      )
      .finally(() => setLoading(false));
  }, [tenantId, runId]);

  if (!tenantId) return <Typography>No tenant selected.</Typography>;

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!run) return null;

  const stages = buildStagesFromRun(run);

  return (
    <Box maxWidth={700}>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate("/runs")}
        sx={{ mb: 2 }}
      >
        Back to History
      </Button>

      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Typography variant="h5">Sync Run</Typography>
        <StatusChip status={run.status} />
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", mb: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Started
            </Typography>
            <Typography>{fmtDate(run.startedAt)}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Completed
            </Typography>
            <Typography>{fmtDate(run.completedAt)}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Total Rows
            </Typography>
            <Typography>{run.totalRows}</Typography>
          </Box>
        </Box>

        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
          <Chip label={`Success: ${run.successCount}`} color="success" size="small" />
          <Chip
            label={`Failed: ${run.failureCount}`}
            color={run.failureCount > 0 ? "error" : "default"}
            size="small"
          />
          <Chip label={`Duplicates: ${run.duplicateCount}`} size="small" />
        </Box>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Stages
        </Typography>
        <StageStepper stages={stages} />
      </Paper>

      {run.sanitizedErrors.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <ErrorTable errors={run.sanitizedErrors} />
        </Paper>
      )}
    </Box>
  );
}
