import { getDefaultRegistry } from "@rjsf/core";
import type { FieldProps } from "@rjsf/utils";
import { DurationField } from "./DurationField";

export const CustomStringField = (props: FieldProps) => {
  const { schema } = props;

  // 检查是否是 duration 格式
  if (schema.format === "duration") {
    return <DurationField {...props} />;
  }

  // 对于其他类型，使用默认的 StringField
  const { fields } = getDefaultRegistry();
  const DefaultStringField = fields.StringField;

  return <DefaultStringField {...props} />;
};
