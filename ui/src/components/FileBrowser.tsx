import { Description, Folder } from "@mui/icons-material";
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Checkbox,
  CircularProgress,
  Link,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  TextField,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import type React from "react";
import { useEffect, useState } from "react";
import type { FileItem } from "@/client";
import { listFilesOptions } from "@/client/@tanstack/react-query.gen";

interface FileBrowserProps {
  /**
   * The initial path to display.
   * @default '.'
   */
  initialPath?: string;
  /**
   * Callback function that is called when the selection is confirmed.
   * @param paths The paths of the selected items.
   */
  onSelect: (paths: string[]) => void;
  /**
   * Whether to allow multiple selections.
   * @default false
   */
  allowMultiple?: boolean;
  /**
   * The type of items that can be selected.
   * @default 'any'
   */
  selectionType?: "file" | "directory" | "mixed";
  /**
   * Whether to show the path input field.
   * @default true
   */
  showPathInput?: boolean;
}

export function FileBrowser({
  initialPath = ".",
  onSelect,
  allowMultiple = false,
  selectionType = "mixed",
  showPathInput = true,
}: FileBrowserProps) {
  const [path, setPath] = useState(initialPath);
  const [pathInputValue, setPathInputValue] = useState(initialPath);
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  useEffect(() => setPathInputValue(path), [path]);

  const { data, error, isLoading, refetch } = useQuery({ ...listFilesOptions({ query: { path } }), retry: false });
  const items = data?.items || [];
  const total = data?.total;

  const isItemSelectable = (item: FileItem) => {
    if (selectionType === "mixed") return true;
    return item.type === selectionType;
  };

  const handleItemClick = (item: FileItem) => {
    if (item.type === "directory") {
      setPath(item.path);
      return;
    }

    if (isItemSelectable(item)) {
      if (allowMultiple) {
        // For single file selection when multi-select is on, just toggle
        handleToggleSelection(item.path);
      } else {
        // Single selection mode
        const newSelectedPaths = new Set([item.path]);
        setSelectedPaths(newSelectedPaths);
      }
    }
  };

  const handleToggleSelection = (path: string) => {
    setSelectedPaths((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    setSelectedPaths((prev) => {
      const newSet = new Set(prev);
      items.filter(isItemSelectable).forEach((item) => newSet.add(item.path));
      return newSet;
    });
  };

  const handleClearAll = () => setSelectedPaths(new Set());

  const handleConfirm = () => {
    if (!allowMultiple && selectionType === "directory") {
      onSelect([path]);
    } else {
      onSelect(Array.from(selectedPaths));
    }
  };

  const handlePathInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPathInputValue(event.target.value);
  };

  const handlePathInputSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const newPath = pathInputValue.trim();
    if (newPath) {
      setPath(newPath);
    }
  };

  const handleBreadcrumbClick = (path: string) => {
    if (path === "$") {
      setPath(initialPath);
      return;
    }
    setPath(path);
  };

  const pathSegments = path.split("/").filter(Boolean);
  const isAbsolute = path.startsWith("/");

  return (
    <Paper elevation={3} sx={{ p: 2, minWidth: 400, maxWidth: 700 }}>
      {showPathInput && (
        <Box component="form" onSubmit={handlePathInputSubmit} sx={{ display: "flex", gap: 1, mb: 1 }}>
          <TextField
            fullWidth
            size="small"
            variant="outlined"
            value={pathInputValue}
            onChange={handlePathInputChange}
            label="Path"
          />
          <Button type="submit" variant="contained" size="small">
            Go
          </Button>
        </Box>
      )}
      <Box sx={{ mb: 1, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ flexGrow: 1 }}>
          <Link
            underline="hover"
            color="inherit"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              handleBreadcrumbClick("$");
            }}
          >
            $
          </Link>
          {pathSegments.map((segment, index) => {
            const path = `${isAbsolute ? "/" : ""}${pathSegments.slice(0, index + 1).join("/")}`;
            return (
              <Link
                underline="hover"
                color="inherit"
                href="#"
                key={path}
                onClick={(e) => {
                  e.preventDefault();
                  handleBreadcrumbClick(path);
                }}
              >
                {segment}
              </Link>
            );
          })}
        </Breadcrumbs>
      </Box>
      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", my: 4 }}>
          <CircularProgress />
        </Box>
      )}
      {error && (
        <Alert
          severity="error"
          sx={{ my: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => refetch()}>
              Retry
            </Button>
          }
        >
          {error instanceof AxiosError
            ? error.response?.data?.detail || error.message
            : "An error occurred while fetching files."}
        </Alert>
      )}
      {total && total > items.length && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          文件过多, 仅显示前 1000 项, 共 {total} 项.
        </Alert>
      )}
      {!isLoading && !error && (
        <List sx={{ maxHeight: 300, overflow: "auto" }}>
          {items.map((item) => {
            const isSelected = selectedPaths.has(item.path);
            const selectable = isItemSelectable(item);
            return (
              <ListItem
                key={item.path}
                disablePadding
                secondaryAction={
                  allowMultiple &&
                  selectable && (
                    <Checkbox edge="end" onChange={() => handleToggleSelection(item.path)} checked={isSelected} />
                  )
                }
              >
                <ListItemButton
                  selected={isSelected}
                  onClick={() => handleItemClick(item)}
                  disabled={!selectable && item.type !== "directory"}
                >
                  <ListItemIcon>{item.type === "directory" ? <Folder /> : <Description />}</ListItemIcon>
                  <ListItemText primary={item.name} />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      )}
      {!isLoading && !error && (
        <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between" }}>
          <Box sx={{ display: "flex", gap: 1 }}>
            {allowMultiple && (
              <>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleSelectAll}
                  disabled={
                    items.filter(isItemSelectable).length === 0 ||
                    items.filter(isItemSelectable).every((item) => selectedPaths.has(item.path))
                  }
                >
                  Select All
                </Button>
                <Button variant="outlined" size="small" onClick={handleClearAll} disabled={selectedPaths.size === 0}>
                  Clear
                </Button>
              </>
            )}
          </Box>
          <Button
            variant="contained"
            onClick={handleConfirm}
            disabled={selectedPaths.size === 0 && (allowMultiple || selectionType !== "directory")}
          >
            {`Confirm${selectedPaths.size > 1 ? ` (${selectedPaths.size})` : ""}`}
          </Button>
        </Box>
      )}
    </Paper>
  );
}
