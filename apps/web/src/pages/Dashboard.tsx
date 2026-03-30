import React from "react";
import { Box, Button, Card, CardContent, Grid, Typography } from "@mui/material";
import CloudIcon from "@mui/icons-material/Cloud";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import HistoryIcon from "@mui/icons-material/History";
import { useNavigate } from "react-router-dom";
import { useTenant } from "../context/TenantContext";

export default function Dashboard() {
  const navigate = useNavigate();
  const { selectedTenant } = useTenant();

  const cards = [
    {
      title: "Salesforce Connection",
      description: "Configure your Salesforce Connected App credentials.",
      icon: <CloudIcon fontSize="large" color="primary" />,
      action: () => navigate("/connection"),
    },
    {
      title: "Run Sync",
      description: "Upload a combined CSV and sync data into Salesforce FSC.",
      icon: <PlayArrowIcon fontSize="large" color="success" />,
      action: () => navigate("/sync"),
    },
    {
      title: "Sync History",
      description: "View past sync runs and their results.",
      icon: <HistoryIcon fontSize="large" color="action" />,
      action: () => navigate("/runs"),
    },
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Dashboard
      </Typography>
      {selectedTenant && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Tenant: <strong>{selectedTenant.name}</strong>
        </Typography>
      )}
      <Grid container spacing={3}>
        {cards.map((card) => (
          <Grid item xs={12} sm={6} md={4} key={card.title}>
            <Card
              sx={{ height: "100%", cursor: "pointer", "&:hover": { boxShadow: 4 } }}
              onClick={card.action}
            >
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1, gap: 1 }}>
                  {card.icon}
                  <Typography variant="h6">{card.title}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {card.description}
                </Typography>
                <Button size="small" sx={{ mt: 2 }} onClick={card.action}>
                  Go
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
