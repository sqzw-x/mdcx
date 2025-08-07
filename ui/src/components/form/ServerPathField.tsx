import { Box, Button, Dialog, DialogContent, InputAdornment, TextField, Typography } from "@mui/material";
import type { FieldProps } from "@rjsf/utils";
import { useState } from "react";
import { FileBrowser } from "../FileBrowser";

type CustomProps = {
  multiple?: boolean;
  type?: "file" | "directory" | "mixed";
  initialPath?: string;
  refField?: string;
};

export const ServerPathField = ({
  uiSchema,
  schema,
  onChange,
  formData,
  label,
  required,
  registry,
  disabled,
  readonly,
}: FieldProps) => {
  const [open, setOpen] = useState(false);
  const { customProps } = uiSchema as { customProps: CustomProps };
  const { title, description } = schema;
  const { multiple = false, type = "mixed", initialPath: initialPathFromUi, refField } = customProps || {};

  const { formContext } = registry;
  const formState = formContext.formData || {};

  const getInitialPath = () => {
    if (refField && formState[refField]) {
      return formState[refField];
    }
    return initialPathFromUi || ".";
  };

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const handleSelect = (paths: string[]) => {
    onChange(multiple ? paths : paths[0]);
    handleClose();
  };

  const displayValue = Array.isArray(formData) ? formData.join(", ") : formData || "";

  return (
    <>
      {title && (
        <Typography variant="subtitle1" component="label" sx={{ fontWeight: 500, mb: 0.5, display: "block" }}>
          {title}
          {required && <span style={{ color: "error.main" }}> *</span>}
        </Typography>
      )}
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {description}
        </Typography>
      )}
      <TextField
        label={label}
        value={displayValue}
        required={required}
        fullWidth
        slotProps={{
          input: {
            readOnly: true,
            endAdornment: (
              <InputAdornment position="end">
                <Button onClick={handleOpen} disabled={disabled || readonly}>
                  选择{type === "file" ? "文件" : type === "directory" ? "目录" : "路径"}
                </Button>
              </InputAdornment>
            ),
          },
        }}
      />
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <FileBrowser
              initialPath={getInitialPath()}
              onSelect={handleSelect}
              allowMultiple={multiple}
              selectionType={type}
            />
          </Box>
        </DialogContent>
      </Dialog>
    </>
  );
};
