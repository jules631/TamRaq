import React from "react";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import { useTenant } from "../context/TenantContext";

interface Props {
  disabled?: boolean;
}

export default function TenantSelector({ disabled }: Props) {
  const { tenants, selectedTenant, setSelectedTenant, loading } = useTenant();

  if (tenants.length <= 1) return null;

  return (
    <FormControl size="small" sx={{ minWidth: 180 }} disabled={disabled || loading}>
      <InputLabel id="tenant-select-label">Tenant</InputLabel>
      <Select
        labelId="tenant-select-label"
        value={selectedTenant?.id ?? ""}
        label="Tenant"
        onChange={(e) => {
          const found = tenants.find((t) => t.id === e.target.value);
          if (found) setSelectedTenant(found);
        }}
      >
        {tenants.map((t) => (
          <MenuItem key={t.id} value={t.id}>
            {t.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
