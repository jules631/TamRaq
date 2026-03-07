import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { CircularProgress, Box } from "@mui/material";
import { ApiProvider } from "./context/ApiContext";
import { TenantProvider } from "./context/TenantContext";
import { SyncRunningProvider, useSyncRunning } from "./context/SyncRunningContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import SalesforceConnection from "./pages/SalesforceConnection";
import Mapping from "./pages/Mapping";
import RunSync from "./pages/RunSync";
import SyncRuns from "./pages/SyncRuns";
import SyncRunDetails from "./pages/SyncRunDetails";

function AppRoutes() {
  const { syncRunning } = useSyncRunning();
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout navDisabled={syncRunning} />}>
          <Route index element={<Dashboard />} />
          <Route path="connection" element={<SalesforceConnection />} />
          <Route path="mapping" element={<Mapping />} />
          <Route path="sync" element={<RunSync />} />
          <Route path="runs" element={<SyncRuns />} />
          <Route path="runs/:runId" element={<SyncRunDetails />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  const { isLoading, isAuthenticated, loginWithRedirect } = useAuth0();

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    loginWithRedirect();
    return null;
  }

  return (
    <ApiProvider>
      <TenantProvider>
        <SyncRunningProvider>
          <AppRoutes />
        </SyncRunningProvider>
      </TenantProvider>
    </ApiProvider>
  );
}
