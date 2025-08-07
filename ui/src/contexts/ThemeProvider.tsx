import { createTheme, ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { createContext, type ReactNode, useEffect, useMemo, useState } from "react";

type ThemeMode = "light" | "dark" | "system";

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      const storedMode = localStorage.getItem("themeMode");
      if (storedMode !== "system" && storedMode !== "light" && storedMode !== "dark") return "system";
      return storedMode;
    }
    return "system";
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const currentTheme = mode === "system" ? systemTheme : mode;

    document.documentElement.classList.toggle("dark", currentTheme === "dark");
    localStorage.setItem("themeMode", mode);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (mode === "system") {
        const newSystemTheme = mediaQuery.matches ? "dark" : "light";
        document.documentElement.classList.toggle("dark", newSystemTheme === "dark");
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  const theme = useMemo(() => {
    if (typeof window === "undefined") {
      return createTheme({ palette: { mode: "dark" } });
    }
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const finalMode = mode === "system" ? systemTheme : mode;

    return createTheme({
      palette: {
        mode: finalMode,
        primary: {
          main: finalMode === "dark" ? "#90caf9" : "#1976d2",
        },
        secondary: {
          main: finalMode === "dark" ? "#f48fb1" : "#dc004e",
        },
        background: {
          default: finalMode === "dark" ? "#020917" : "#fafafa",
          paper: finalMode === "dark" ? "#1e1e1e" : "#ffffff",
        },
      },
    });
  }, [mode]);

  return (
    <ThemeContext.Provider value={{ mode, setMode }}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
