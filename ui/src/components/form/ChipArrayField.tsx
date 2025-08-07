import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Add, Cancel } from "@mui/icons-material";
import {
  Autocomplete,
  Box,
  Chip,
  FormControl,
  FormHelperText,
  IconButton,
  Input,
  InputLabel,
  Menu,
  OutlinedInput,
  TextField,
} from "@mui/material";
import { getDefaultRegistry } from "@rjsf/core";
import type { FieldProps, RJSFSchema } from "@rjsf/utils";
import { forwardRef, type KeyboardEvent, useEffect, useState } from "react";

/**
 * 自定义 ArrayField 组件.
 *
 * 对于 enum[] ｜ string[] 字段, 使用 Chip 组件, 否则回退到默认实现.
 */
export const CustomArrayField = (props: FieldProps) => {
  const { schema } = props;

  // 不是我们处理的类型, 回退到默认实现
  // 此处实际上存在未处理的边缘情况, 如混合类型数组, 但应该不会遇到. 实际上, 目前回退情况也不会发生.
  if (
    !schema.items ||
    Array.isArray(schema.items) ||
    typeof schema.items === "boolean" ||
    schema.items.type !== "string"
  ) {
    const { ArrayField } = getDefaultRegistry().fields;
    return <ArrayField {...props} />;
  }

  return <ChipArrayField {...props} />;
};

const DivAsInput = forwardRef<HTMLDivElement, { children?: React.ReactNode }>((props, ref) => (
  <div ref={ref} {...props} />
));
DivAsInput.displayName = "DivAsInput";

const ChipArrayField = ({ schema, uiSchema, onChange, formData, rawErrors, idSchema, label, required }: FieldProps) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const { title } = schema;
  const itemSchema = schema.items as RJSFSchema;
  // 限定: enum 字段只允许 string[], 需在生成schema时保证. 当 enum 不存在时为 string[].
  const enumOptions = itemSchema.enum as string[] | undefined;
  const [data, setData] = useState((formData as string[]) || []);
  const enumNames = (itemSchema.showNames || enumOptions) as string[] | undefined; // 约定使用 showNames 字段定义显示名称
  const unused = enumOptions?.filter((opt) => !data.includes(opt));
  useEffect(() => onChange(data), [data, onChange]);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleDelete = (valueToDelete: string) => {
    setData((prevData) => prevData.filter((value) => value !== valueToDelete));
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = data.indexOf(active.id as string);
      const newIndex = data.indexOf(over.id as string);
      setData(arrayMove(data, oldIndex, newIndex));
    }
  };

  const handleOptionClick = (value: string) => {
    setData((prevData) => [...prevData, value]);
    setInputValue("");
    // setData 的结果不会立即反映在 unused 中, 因此 unused.length===1 即表明这是最后一个选项
    if (unused?.length === 1) {
      setAnchorEl(null);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.nativeEvent.isComposing && inputValue) {
      event.preventDefault();
      if (!data.includes(inputValue)) {
        setData([...data, inputValue]);
        setInputValue("");
      }
    }
    if (event.key === "Backspace" && !inputValue && data.length > 0) {
      event.preventDefault();
      const newData = [...data];
      newData.pop(); // 删除最后一个元素
      setData(newData);
    }
  };

  const getEnumName = (value: string) => {
    if (enumOptions && enumNames) {
      const index = enumOptions.indexOf(value);
      return enumNames[index] ?? value;
    }
    return value;
  };

  const activeChipName = activeId ? getEnumName(activeId) : "";

  return (
    <FormControl fullWidth error={!!rawErrors?.length}>
      <InputLabel id={`${idSchema.$id}-label`} shrink>
        {uiSchema?.["ui:title"] || title || label}
        {required ? "*" : ""}
      </InputLabel>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <OutlinedInput
          label={uiSchema?.["ui:title"] || title || label}
          notched
          multiline
          sx={{
            padding: "16.5px 14px",
            "& .MuiOutlinedInput-input": { padding: 0, display: "flex", flexWrap: "wrap", gap: 0.5 },
          }}
          inputComponent={DivAsInput}
          inputProps={{
            children: (
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                <SortableContext items={data}>
                  {data.map((value) => (
                    <SortableChip key={value} value={value} name={getEnumName(value)} onDelete={handleDelete} />
                  ))}
                </SortableContext>
                {enumOptions && unused?.length ? (
                  <>
                    <IconButton size="small" onClick={(e) => setAnchorEl(e.currentTarget)}>
                      <Add />
                    </IconButton>
                    <Menu
                      anchorEl={anchorEl}
                      open={open}
                      onClose={() => setAnchorEl(null)}
                      slotProps={{ paper: { style: { maxHeight: 48 * 4.5, width: 250 } } }}
                    >
                      <Autocomplete
                        options={unused}
                        getOptionLabel={getEnumName}
                        disableCloseOnSelect
                        inputValue={inputValue}
                        onInputChange={(_, value, reason) => {
                          if (reason === "input") {
                            setInputValue(value);
                          }
                        }}
                        onChange={(_, value) => value && handleOptionClick(value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            autoFocus
                            placeholder="选择或输入值"
                            onKeyDown={handleKeyDown}
                            value={inputValue}
                          />
                        )}
                      />
                    </Menu>
                  </>
                ) : (
                  <Input
                    disableUnderline
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    sx={{ flex: 1, minWidth: "50px", padding: "2px 4px" }}
                  />
                )}
              </Box>
            ),
          }}
        />
        <DragOverlay>{activeId ? <Chip label={activeChipName} /> : null}</DragOverlay>
      </DndContext>
      {rawErrors && rawErrors.length > 0 && <FormHelperText>{rawErrors.join(", ")}</FormHelperText>}
    </FormControl>
  );
};

const SortableChip = ({
  value,
  name,
  onDelete,
}: {
  value: string;
  name: string;
  onDelete: (value: string) => void;
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: value });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0 : 1,
  };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Chip
        label={name}
        onDelete={() => onDelete(value)}
        deleteIcon={<Cancel onPointerDown={(e) => e.stopPropagation()} />}
      />
    </div>
  );
};
