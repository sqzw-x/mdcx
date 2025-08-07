import { defineConfig } from "@rsbuild/core";
import { pluginReact } from "@rsbuild/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/rspack";

export default defineConfig({
  plugins: [pluginReact()],
  tools: {
    rspack: {
      plugins: [tanstackRouter({ target: "react", autoCodeSplitting: true })],
    },
  },
  source: {
    define: {
      "process.env.PUBLIC_DEV_ENABLE_WS": JSON.stringify(true),
    },
  },
  server: {
    port: 3010,
  },
});
