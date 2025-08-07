import type { RegistryFieldsType } from "@rjsf/utils";
import { CustomArrayField } from "./ChipArrayField";
import { CustomStringField } from "./CustomStringField";
import { ServerPathField } from "./ServerPathField";

export const fields: RegistryFieldsType = {
  ArrayField: CustomArrayField,
  StringField: CustomStringField,
  serverPath: ServerPathField,
};
