import React from "react";
import Chip from "@mui/material/Chip";

const STATUS_MAP: Record<string, { color: "default" | "info" | "success" | "warning" | "error"; label: string }> = {
  pending: { color: "default", label: "Pending" },
  running: { color: "info", label: "Running" },
  success: { color: "success", label: "Success" },
  partial: { color: "warning", label: "Partial" },
  failed: { color: "error", label: "Failed" },
  unknown: { color: "default", label: "Unknown" },
};

interface Props {
  status: string;
}

export default function StatusChip({ status }: Props) {
  const cfg = STATUS_MAP[status] ?? STATUS_MAP.unknown;
  return <Chip label={cfg.label} color={cfg.color} size="small" />;
}
