import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  TextField,
  Typography,
  InputLabel,
  FormControl,
} from "@mui/material";
import { useApi } from "../context/ApiContext";
import { useTenant } from "../context/TenantContext";
import type { LinkField, RecordType, SyncConfigIn } from "../api/types";

export default function Mapping() {
  const api = useApi();
  const { selectedTenant } = useTenant();
  const tenantId = selectedTenant?.id ?? "";

  const [recordTypes, setRecordTypes] = useState<RecordType[]>([]);
  const [linkFields, setLinkFields] = useState<LinkField[]>([]);
  const [form, setForm] = useState<SyncConfigIn>({
    householdAccountRecordTypeId: null,
    financialAccountHouseholdLookupFieldApiName: null,
    enablePositions: true,
  });
  const [loadingMeta, setLoadingMeta] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    // Load existing config
    api.getSyncConfig(tenantId).then((cfg) => {
      setForm({
        householdAccountRecordTypeId: cfg.householdAccountRecordTypeId,
        financialAccountHouseholdLookupFieldApiName:
          cfg.financialAccountHouseholdLookupFieldApiName,
        enablePositions: cfg.enablePositions,
      });
    }).catch(() => {});
  }, [tenantId]);

  const loadMetadata = async () => {
    if (!tenantId) return;
    setLoadingMeta(true);
    setError(null);
    try {
      const [rts, lfs] = await Promise.all([
        api.getAccountRecordTypes(tenantId),
        api.getLinkFields(tenantId),
      ]);
      setRecordTypes(rts);
      setLinkFields(lfs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load Salesforce metadata");
    } finally {
      setLoadingMeta(false);
    }
  };

  const handleSave = async () => {
    if (!tenantId) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await api.putSyncConfig(tenantId, form);
      setSaved(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (!tenantId) return <Typography>No tenant selected.</Typography>;

  return (
    <Box maxWidth={600}>
      <Typography variant="h5" gutterBottom>
        Sync Mapping
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={loadMetadata}
            disabled={loadingMeta}
          >
            {loadingMeta ? <CircularProgress size={16} /> : "Load from Salesforce"}
          </Button>
        </Box>

        <FormControl fullWidth margin="normal">
          <InputLabel id="rt-label">Household Account Record Type</InputLabel>
          <Select
            labelId="rt-label"
            label="Household Account Record Type"
            value={form.householdAccountRecordTypeId ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, householdAccountRecordTypeId: e.target.value || null }))
            }
          >
            <MenuItem value="">-- none --</MenuItem>
            {recordTypes.map((rt) => (
              <MenuItem key={rt.id} value={rt.id}>
                {rt.name} ({rt.developerName})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth margin="normal">
          <InputLabel id="lf-label">FinancialAccount → Household Lookup Field</InputLabel>
          <Select
            labelId="lf-label"
            label="FinancialAccount → Household Lookup Field"
            value={form.financialAccountHouseholdLookupFieldApiName ?? ""}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                financialAccountHouseholdLookupFieldApiName: e.target.value || null,
              }))
            }
          >
            <MenuItem value="">-- none --</MenuItem>
            {linkFields.map((lf) => (
              <MenuItem key={lf.apiName} value={lf.apiName}>
                {lf.label} ({lf.apiName})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          sx={{ mt: 2 }}
          control={
            <Switch
              checked={form.enablePositions}
              onChange={(e) =>
                setForm((f) => ({ ...f, enablePositions: e.target.checked }))
              }
            />
          }
          label="Sync Positions (Asset records)"
        />

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {saved && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Mapping saved.
          </Alert>
        )}

        <Box sx={{ mt: 3 }}>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? <CircularProgress size={20} /> : "Save Mapping"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
