import { FormControl, Typography } from "@mui/material";
import { Form } from "@rjsf/mui";
import type { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import {
  getConfigSchemaOptions,
  getConfigUiSchemaOptions,
  getCurrentConfigOptions,
} from "@/client/@tanstack/react-query.gen";
import { fields } from "@/components/form";

export const Route = createFileRoute("/settings")({
  component: SettingsComponent,
});

function SettingsComponent() {
  const configQ = useQuery(getCurrentConfigOptions());
  const schemaQ = useQuery(getConfigSchemaOptions());
  const uiSchemaQ = useQuery(getConfigUiSchemaOptions());

  return (
    schemaQ.isSuccess &&
    configQ.isSuccess &&
    uiSchemaQ.isSuccess && (
      <div className="p-2">
        <Typography variant="h4" gutterBottom>
          设置
        </Typography>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <Form
            schema={schemaQ.data as RJSFSchema}
            uiSchema={uiSchemaQ.data}
            validator={validator}
            formData={configQ.data}
            fields={fields}
            onSubmit={() => {}}
          />
        </FormControl>
      </div>
    )
  );
}
