import React from "react";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

export interface ErrorEntry {
  stage: string;
  externalIdHash: string;
  message: string;
}

interface Props {
  errors: ErrorEntry[];
}

export default function ErrorTable({ errors }: Props) {
  if (errors.length === 0) return null;

  return (
    <>
      <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
        Record Errors ({errors.length})
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Stage</TableCell>
              <TableCell>ID Hash</TableCell>
              <TableCell>Message</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {errors.map((err, i) => (
              <TableRow key={i}>
                <TableCell>{err.stage}</TableCell>
                <TableCell sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                  {err.externalIdHash.slice(0, 12)}…
                </TableCell>
                <TableCell>{err.message}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
