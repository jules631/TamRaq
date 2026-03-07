import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useApi } from "../context/ApiContext";
import { useTenant } from "../context/TenantContext";
import type { SalesforceConfigIn, TestConnectionOut } from "../api/types";

const EMPTY: SalesforceConfigIn = {
  loginUrl: "https://test.salesforce.com",
  clientId: "",
  integrationUsername: "",
  privateKeyPem: "",
};

export default function SalesforceConnection() {
  const api = useApi();
  const { selectedTenant } = useTenant();
  const tenantId = selectedTenant?.id ?? "";

  const [form, setForm] = useState<SalesforceConfigIn>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!tenantId) return;
    api.getSalesforceConfig(tenantId).then((cfg) => {
      setForm((f) => ({
        ...f,
        loginUrl: cfg.loginUrl,
        clientId: cfg.clientId,
        integrationUsername: cfg.integrationUsername,
      }));
    }).catch(() => {});
  }, [tenantId]);

  const handleChange = (field: keyof SalesforceConfigIn) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSave = async () => {
    if (!tenantId) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await api.putSalesforceConfig(tenantId, form);
      setSaved(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!tenantId) return;
    setTesting(true);
    setError(null);
    setTestResult(null);
    try {
      const result = await api.testConnection(tenantId);
      setTestResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Test failed");
    } finally {
      setTesting(false);
    }
  };

  if (!tenantId) return <Typography>No tenant selected.</Typography>;

  return (
    <Box maxWidth={600}>
      <Typography variant="h5" gutterBottom>
        Salesforce Connection
      </Typography>
      <Paper sx={{ p: 3 }}>
        <TextField
          label="Login URL"
          value={form.loginUrl}
          onChange={handleChange("loginUrl")}
          fullWidth
          margin="normal"
          helperText="e.g. https://test.salesforce.com for sandboxes"
        />
        <TextField
          label="Connected App Client ID"
          value={form.clientId}
          onChange={handleChange("clientId")}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Integration Username"
          value={form.integrationUsername}
          onChange={handleChange("integrationUsername")}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Private Key (PEM)"
          value={form.privateKeyPem}
          onChange={handleChange("privateKeyPem")}
          fullWidth
          margin="normal"
          multiline
          minRows={6}
          placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"
          helperText="Paste the RSA private key for the Connected App. Stored encrypted."
        />
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {saved && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Configuration saved.
          </Alert>
        )}
        {testResult && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Connected: org {testResult.orgId} | user {testResult.username}
          </Alert>
        )}
        <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? <CircularProgress size={20} /> : "Save"}
          </Button>
          <Button
            variant="outlined"
            onClick={handleTest}
            disabled={testing}
          >
            {testing ? <CircularProgress size={20} /> : "Test Connection"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
