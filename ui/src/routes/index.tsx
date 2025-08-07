import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { FileBrowser } from "../components/FileBrowser";

export const Route = createFileRoute("/")({
  component: Index,
});

function createData(name: string, value: string) {
  return { name, value };
}

const rows = [
  createData("Project", "MDCX"),
  createData("Version", "1.0.0"),
  createData("Author", "srz"),
  createData("License", "MIT"),
];

function Index() {
  const [selectedPaths, setSelectedPaths] = useState<string[] | null>(null);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Value</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.name} sx={{ "&:last-child td, &:last-child th": { border: 0 } }}>
                <TableCell component="th" scope="row">
                  {row.name}
                </TableCell>
                <TableCell align="right">{row.value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <FileBrowser onSelect={(paths) => setSelectedPaths(paths)} selectionType="directory" />

      {selectedPaths?.map((path, index) => (
        <Typography key={path} variant="body1">
          Selected Path {index + 1}: <strong>{path}</strong>
        </Typography>
      ))}
    </Box>
  );
}
