import { Box, InputAdornment, TextField, Typography } from "@mui/material";
import type { FieldProps } from "@rjsf/utils";
import { useEffect, useState } from "react";

// 解析 ISO 8601 duration 格式 (PT1H2M3S) 到小时、分钟、秒
const parseDuration = (duration: string): { hours: number; minutes: number; seconds: number } => {
  if (!duration || !duration.startsWith("PT")) {
    return { hours: 0, minutes: 0, seconds: 0 };
  }

  const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) {
    return { hours: 0, minutes: 0, seconds: 0 };
  }

  return {
    hours: parseInt(match[1] || "0", 10),
    minutes: parseInt(match[2] || "0", 10),
    seconds: parseInt(match[3] || "0", 10),
  };
};

// 将小时、分钟、秒格式化为 ISO 8601 duration 格式
const formatDuration = (hours: number, minutes: number, seconds: number): string => {
  if (hours === 0 && minutes === 0 && seconds === 0) {
    return "PT0S";
  }

  let result = "PT";
  if (hours > 0) result += `${hours}H`;
  if (minutes > 0) result += `${minutes}M`;
  if (seconds > 0) result += `${seconds}S`;

  return result;
};

export const DurationField = ({ schema, onChange, formData, required, disabled, readonly }: FieldProps) => {
  const { title, description } = schema;
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);

  // 当 formData 变化时，解析 duration 并更新内部状态
  useEffect(() => {
    if (formData) {
      const parsed = parseDuration(formData);
      setHours(parsed.hours);
      setMinutes(parsed.minutes);
      setSeconds(parsed.seconds);
    } else {
      setHours(0);
      setMinutes(0);
      setSeconds(0);
    }
  }, [formData]);

  // 处理输入变化
  const handleChange = (newHours: number, newMinutes: number, newSeconds: number) => {
    setHours(newHours);
    setMinutes(newMinutes);
    setSeconds(newSeconds);

    const durationString = formatDuration(newHours, newMinutes, newSeconds);
    onChange(durationString);
  };

  const handleHoursChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(0, parseInt(event.target.value || "0", 10));
    handleChange(value, minutes, seconds);
  };

  const handleMinutesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(0, Math.min(59, parseInt(event.target.value || "0", 10)));
    handleChange(hours, value, seconds);
  };

  const handleSecondsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(0, Math.min(59, parseInt(event.target.value || "0", 10)));
    handleChange(hours, minutes, value);
  };

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
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <TextField
          label="小时"
          type="number"
          value={hours}
          onChange={handleHoursChange}
          disabled={disabled}
          slotProps={{
            input: { endAdornment: <InputAdornment position="end">时</InputAdornment> },
            htmlInput: { readOnly: readonly, min: 0, step: 1 },
          }}
          size="small"
          sx={{ width: 100 }}
        />
        <TextField
          label="分钟"
          type="number"
          value={minutes}
          onChange={handleMinutesChange}
          disabled={disabled}
          slotProps={{
            input: { endAdornment: <InputAdornment position="end">分</InputAdornment> },
            htmlInput: { readOnly: readonly, min: 0, max: 59, step: 1 },
          }}
          size="small"
          sx={{ width: 100 }}
        />
        <TextField
          label="秒"
          type="number"
          value={seconds}
          onChange={handleSecondsChange}
          disabled={disabled}
          slotProps={{
            input: { endAdornment: <InputAdornment position="end">秒</InputAdornment> },
            htmlInput: { readOnly: readonly, min: 0, max: 59, step: 1 },
          }}
          size="small"
          sx={{ width: 100 }}
        />
      </Box>
    </>
  );
};
