import React from "react";
import {
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import CloudIcon from "@mui/icons-material/Cloud";
import DashboardIcon from "@mui/icons-material/Dashboard";
import MapIcon from "@mui/icons-material/Map";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import HistoryIcon from "@mui/icons-material/History";
import { useNavigate, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "SF Connection", path: "/connection", icon: <CloudIcon /> },
  { label: "Mapping", path: "/mapping", icon: <MapIcon /> },
  { label: "Run Sync", path: "/sync", icon: <PlayArrowIcon /> },
  { label: "Sync History", path: "/runs", icon: <HistoryIcon /> },
];

interface Props {
  disabled?: boolean;
}

export default function SideNav({ disabled }: Props) {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <div>
      <Toolbar>
        <Typography variant="subtitle2" noWrap sx={{ fontWeight: 700, letterSpacing: 1 }}>
          Tamarac FSC
        </Typography>
      </Toolbar>
      <Divider />
      <List dense>
        {NAV_ITEMS.map((item) => (
          <ListItemButton
            key={item.path}
            selected={pathname === item.path}
            disabled={disabled}
            onClick={() => navigate(item.path)}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </div>
  );
}
