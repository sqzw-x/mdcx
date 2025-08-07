import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8000/openapi.json",
  output: "src/client",
  plugins: [
    "@hey-api/client-axios",
    "@tanstack/react-query",
    {
      name: "@hey-api/schemas",
      type: "json",
    },
  ],
});
