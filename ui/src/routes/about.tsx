import { Paper, Typography } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/about")({
  component: About,
});

function About() {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        MDCX WebUI
      </Typography>
      <Typography variant="body1">This is a web interface for MDCX server.</Typography>
    </Paper>
  );
}
