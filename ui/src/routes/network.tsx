import { Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/network")({
  component: NetworkComponent,
});

function createData(property: string, value: string) {
  return { property, value };
}

const rows = [
  createData("IP Address", "192.168.1.100"),
  createData("Subnet Mask", "255.255.255.0"),
  createData("Default Gateway", "192.168.1.1"),
  createData("DNS Server", "8.8.8.8"),
];

function NetworkComponent() {
  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="network table">
        <TableHead>
          <TableRow>
            <TableCell>Property</TableCell>
            <TableCell align="right">Value</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.property} sx={{ "&:last-child td, &:last-child th": { border: 0 } }}>
              <TableCell component="th" scope="row">
                {row.property}
              </TableCell>
              <TableCell align="right">{row.value}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
