import React from "react";
import {
  Step,
  StepLabel,
  Stepper,
  Typography,
  Box,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import CircularProgress from "@mui/material/CircularProgress";
import ErrorIcon from "@mui/icons-material/Error";

export type StageStatus = "pending" | "started" | "done" | "error";

export interface StageInfo {
  id: string;
  label: string;
  status: StageStatus;
  detail?: string;
}

interface Props {
  stages: StageInfo[];
}

function StageIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case "done":
      return <CheckCircleIcon color="success" />;
    case "started":
      return <CircularProgress size={20} />;
    case "error":
      return <ErrorIcon color="error" />;
    default:
      return <RadioButtonUncheckedIcon color="disabled" />;
  }
}

export default function StageStepper({ stages }: Props) {
  const activeIndex = stages.findIndex((s) => s.status === "started");
  const step = activeIndex >= 0 ? activeIndex : stages.filter((s) => s.status === "done").length;

  return (
    <Stepper activeStep={step} orientation="vertical">
      {stages.map((stage) => (
        <Step key={stage.id} completed={stage.status === "done"}>
          <StepLabel
            icon={<StageIcon status={stage.status} />}
            optional={
              stage.detail ? (
                <Typography variant="caption">{stage.detail}</Typography>
              ) : undefined
            }
          >
            {stage.label}
          </StepLabel>
        </Step>
      ))}
    </Stepper>
  );
}
