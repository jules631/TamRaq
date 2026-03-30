import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
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

interface ChangeRow {
  object: string;
  operation: string;
  count: number;
  stage: string;
}

function buildChangeRows(run: SyncRunOut): ChangeRow[] {
  const rows: ChangeRow[] = [];
  const sc = run.stageCounts;

  if (sc.upsert_households?.processed != null)
    rows.push({ object: "Account (Household)", operation: "Upsert", count: sc.upsert_households.processed, stage: "upsert_households" });
  if (sc.upsert_contacts?.processed != null)
    rows.push({ object: "Contact", operation: "Upsert", count: sc.upsert_contacts.processed, stage: "upsert_contacts" });
  if (sc.upsert_acr?.processed != null)
    rows.push({ object: "AccountContactRelation", operation: "Insert", count: sc.upsert_acr.processed, stage: "upsert_acr" });
  if (sc.upsert_financial_accounts?.processed != null)
    rows.push({ object: "FinancialAccount", operation: "Upsert", count: sc.upsert_financial_accounts.processed, stage: "upsert_financial_accounts" });
  if (run.enablePositions && sc.upsert_positions?.processed != null)
    rows.push({ object: "FinancialHolding", operation: "Upsert", count: sc.upsert_positions.processed, stage: "upsert_positions" });

  return rows;
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
  const [tab, setTab] = useState(0);

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
  const changeRows = buildChangeRows(run);

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

      {/* Summary bar */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", mb: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">Started</Typography>
            <Typography>{fmtDate(run.startedAt)}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Completed</Typography>
            <Typography>{fmtDate(run.completedAt)}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Total Rows</Typography>
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

      {/* Tabs */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Stages" />
        <Tab label="Changes" />
        {run.sanitizedErrors.length > 0 && <Tab label={`Errors (${run.sanitizedErrors.length})`} />}
      </Tabs>

      {tab === 0 && (
        <Paper sx={{ p: 3 }}>
          <StageStepper stages={stages} />
        </Paper>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 3 }}>
          {changeRows.length === 0 ? (
            <Typography color="text.secondary">No records were written.</Typography>
          ) : (
            <>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Salesforce Object</strong></TableCell>
                    <TableCell><strong>Operation</strong></TableCell>
                    <TableCell align="right"><strong>Records</strong></TableCell>
                    <TableCell align="right"><strong>Outcome</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {changeRows.map((row) => {
                    const hasError = run.sanitizedErrors.some((e) => e.stage === row.stage);
                    return (
                      <TableRow key={row.stage}>
                        <TableCell>{row.object}</TableCell>
                        <TableCell>
                          <Chip
                            label={row.operation}
                            size="small"
                            variant="outlined"
                            color={row.operation === "Insert" ? "info" : "default"}
                          />
                        </TableCell>
                        <TableCell align="right">{row.count}</TableCell>
                        <TableCell align="right">
                          {hasError ? (
                            <ErrorOutlineIcon fontSize="small" color="error" />
                          ) : (
                            <CheckCircleOutlineIcon fontSize="small" color="success" />
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: "divider" }}>
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  Parsed from CSV
                </Typography>
                <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
                  {run.stageCounts.parse_and_validate &&
                    Object.entries(run.stageCounts.parse_and_validate)
                      .filter(([k]) => k !== "rows")
                      .map(([k, v]) => (
                        <Box key={k}>
                          <Typography variant="caption" color="text.secondary" sx={{ textTransform: "capitalize" }}>
                            {k.replace(/([A-Z])/g, " $1")}
                          </Typography>
                          <Typography variant="body2" fontWeight={500}>{v}</Typography>
                        </Box>
                      ))}
                </Box>
              </Box>
            </>
          )}
        </Paper>
      )}

      {tab === 2 && run.sanitizedErrors.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <ErrorTable errors={run.sanitizedErrors} />
        </Paper>
      )}
    </Box>
  );
}
