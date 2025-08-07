import {
  Article,
  Brightness4,
  Brightness7,
  BrightnessAuto,
  Build,
  ChevronLeft,
  ChevronRight,
  Home,
  Info,
  Lan,
  Menu,
  Settings,
} from "@mui/icons-material";
import {
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  AppBar as MuiAppBar,
  type AppBarProps as MuiAppBarProps,
  styled,
  Toolbar,
  Typography,
} from "@mui/material";
import { Link } from "@tanstack/react-router";
import { type ReactNode, useState } from "react";
import { useTheme } from "@/hooks/useTheme";
import type { FileRouteTypes } from "@/routeTree.gen";

const drawerWidth = 240;
const collapsedDrawerWidth = 60;

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })(({ theme }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create("margin", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: 0,
}));

interface AppBarProps extends MuiAppBarProps {
  open?: boolean;
}

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== "open",
})<AppBarProps>(({ theme, open }) => ({
  transition: theme.transitions.create(["margin", "width"], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: "flex-end",
}));

const createMenuItems = <
  T extends readonly {
    text: string;
    to: FileRouteTypes["to"];
    icon: ReactNode;
  }[],
>(
  items: T,
) => items;

export default function Layout({ children }: { children: ReactNode }) {
  const { mode, setMode } = useTheme();
  const [open, setOpen] = useState(true);

  const handleThemeChange = () => {
    const newMode = mode === "light" ? "dark" : mode === "dark" ? "system" : "light";
    setMode(newMode);
  };

  const menuItems = createMenuItems([
    { text: "Home", to: "/", icon: <Home /> },
    { text: "Tool", to: "/tool", icon: <Build /> },
    { text: "Network", to: "/network", icon: <Lan /> },
    { text: "Logs", to: "/logs", icon: <Article /> },
    { text: "Settings", to: "/settings", icon: <Settings /> },
    { text: "About", to: "/about", icon: <Info /> },
  ]);

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={() => setOpen(!open)}
            edge="start"
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Dashboard
          </Typography>
          <IconButton color="inherit" onClick={handleThemeChange}>
            {mode === "light" ? <Brightness7 /> : mode === "dark" ? <Brightness4 /> : <BrightnessAuto />}
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: open ? drawerWidth : collapsedDrawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: open ? drawerWidth : collapsedDrawerWidth,
            boxSizing: "border-box",
            transition: "width 0.2s",
          },
        }}
        variant="persistent"
        anchor="left"
        open={true}
      >
        <DrawerHeader>
          <IconButton onClick={() => setOpen(!open)}>{open ? <ChevronLeft /> : <ChevronRight />}</IconButton>
        </DrawerHeader>
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.to} disablePadding>
              <ListItemButton component={Link} to={item.to} activeProps={{ style: { fontWeight: "bold" } }}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <Main>
        <DrawerHeader />
        {children}
      </Main>
    </Box>
  );
}
