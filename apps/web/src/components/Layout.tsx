import React, { useState } from "react";
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  Toolbar,
  Typography,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import LogoutIcon from "@mui/icons-material/Logout";
import { Outlet } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import SideNav from "./SideNav";
import TenantSelector from "./TenantSelector";

const DRAWER_WIDTH = 220;

interface Props {
  navDisabled?: boolean;
}

export default function Layout({ navDisabled }: Props) {
  const { logout } = useAuth0();
  const theme = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const drawer = <SideNav disabled={navDisabled} />;

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: theme.zIndex.drawer + 1 }}
        elevation={1}
      >
        <Toolbar variant="dense">
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 1, display: { md: "none" } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, fontSize: "1rem" }}>
            Tamarac FSC Connector
          </Typography>
          <TenantSelector disabled={navDisabled} />
          <IconButton
            color="inherit"
            onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
            sx={{ ml: 1 }}
            title="Sign out"
          >
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", md: "block" },
          width: DRAWER_WIDTH,
          flexShrink: 0,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        {drawer}
      </Drawer>

      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH },
        }}
      >
        {drawer}
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: "48px",
          minHeight: "calc(100vh - 48px)",
          bgcolor: "grey.50",
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
