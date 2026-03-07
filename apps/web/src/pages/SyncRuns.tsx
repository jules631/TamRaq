import React, { useEffect, useState } from "react";
import {
  Box,
  CircularProgress,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
} from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useNavigate } from "react-router-dom";
import { useApi } from "../context/ApiContext";
import { useTenant } from "../context/TenantContext";
import StatusChip from "../components/StatusChip";
import type { SyncRunListItem } from "../api/types";

function fmtDate(dt: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

export default function SyncRuns() {
  const api = useApi();
  const { selectedTenant } = useTenant();
  const navigate = useNavigate();
  const tenantId = selectedTenant?.id ?? "";

  const [runs, setRuns] = useState<SyncRunListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.listSyncRuns(tenantId);
      setRuns(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load runs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [tenantId]);

  if (!tenantId) return <Typography>No tenant selected.</Typography>;

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        <Typography variant="h5">Sync History</Typography>
        <IconButton onClick={load} disabled={loading} size="small">
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Started</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Rows</TableCell>
                <TableCell align="right">Success</TableCell>
                <TableCell align="right">Failed</TableCell>
                <TableCell align="right">Dupes</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No sync runs yet
                  </TableCell>
                </TableRow>
              )}
              {runs.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{fmtDate(run.startedAt)}</TableCell>
                  <TableCell>
                    <StatusChip status={run.status} />
                  </TableCell>
                  <TableCell align="right">{run.totalRows}</TableCell>
                  <TableCell align="right">{run.successCount}</TableCell>
                  <TableCell align="right">{run.failureCount}</TableCell>
                  <TableCell align="right">{run.duplicateCount}</TableCell>
                  <TableCell>{fmtDate(run.completedAt)}</TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/runs/${run.id}`)}
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
