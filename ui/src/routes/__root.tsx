import { createRootRoute, Outlet, useLocation, useNavigate } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { useEffect, useState } from "react";
import { client } from "@/client/client.gen";
import { getWebSocketConnections } from "@/client/sdk.gen";
import { WebSocketProvider } from "@/contexts/WebSocketProvider";
import Layout from "../components/Layout";

export const Route = createRootRoute({
  component: () => {
    const navigate = useNavigate();
    const location = useLocation();
    const apiKey = localStorage.getItem("apiKey");
    const [isValidated, setIsValidated] = useState(false);
    const isAuthPage = location.pathname === "/auth";

    useEffect(() => {
      if (isAuthPage) {
        return;
      }
      if (apiKey) {
        client.setConfig({ baseURL: import.meta.env.PROD ? "" : import.meta.env.PUBLIC_DEV_API_URL, auth: apiKey });
        console.debug(`Base URL: ${import.meta.env.PUBLIC_DEV_API_URL}`);
        // Perform a check on startup
        getWebSocketConnections()
          .then(() => {
            setIsValidated(true);
          })
          .catch((e) => {
            console.error("Failed to fetch connections:", e);
            // If the API key is invalid, redirect to auth page
            localStorage.removeItem("apiKey");
            navigate({ to: "/auth", replace: true });
          });
      } else {
        navigate({ to: "/auth", replace: true });
      }
    }, [apiKey, navigate, isAuthPage]);

    console.log(`isValidated: ${isValidated}, isAuthPage: ${isAuthPage}`);
    if (isAuthPage) return <Outlet />;

    return (
      <>
        <Layout>
          <WebSocketProvider>
            <Outlet />
          </WebSocketProvider>
        </Layout>
        <TanStackRouterDevtools />
      </>
    );
  },
});
