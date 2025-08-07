/// <reference types="@rsbuild/core/types" />

/**
 * Imports the SVG file as a React component.
 * @requires [@rsbuild/plugin-svgr](https://npmjs.com/package/@rsbuild/plugin-svgr)
 */
declare module "*.svg?react" {
  import type React from "react";
  const ReactComponent: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
  export default ReactComponent;
}

declare interface ImportMetaEnv {
  readonly PUBLIC_DEV_API_URL: string;
  readonly PUBLIC_DEV_WS_URL: string;
  readonly PUBLIC_DEV_ENABLE_WS: "true" | "false";
}
