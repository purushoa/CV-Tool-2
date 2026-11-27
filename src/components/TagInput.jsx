
import React, { useState } from "react";
import { Plus, X } from "lucide-react";

export function TagInput({
  items,
  values,
  onChange,
  placeholder
}) {
  const [value, setValue] = useState("");

  // Support both items and values safely
  const tags = Array.isArray(items)
    ? items
    : Array.isArray(values)
    ? values
    : [];

  // Add a new item
  const add = () => {
    const item = value.trim();

    if (
      item &&
      !tags.some(
        x =>
          String(x).toLowerCase() ===
          item.toLowerCase()
      )
    ) {
      onChange([...tags, item]);
    }

    setValue("");
  };

  return (
    <div>

      <div className="flex gap-2">

        <input
          className="field"
          value={value}
          placeholder={placeholder}
          onChange={e =>
            setValue(e.target.value)
          }
          onKeyDown={e => {
            if (
              e.key === "Enter" ||
              e.key === ","
            ) {
              e.preventDefault();
              add();
            }
          }}
        />

        <button
          type="button"
          className="btn-outline shrink-0"
          onClick={add}
        >
          <Plus size={17} />
          Add
        </button>

      </div>

      <div className="mt-3 flex flex-wrap gap-2">

        {tags.map(x => (
          <span
            key={x}
            className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700"
          >
            {x}

            <button
              type="button"
              aria-label={`Remove ${x}`}
              onClick={() =>
                onChange(
                  tags.filter(y => y !== x)
                )
              }
            >
              <X size={14} />
            </button>

          </span>
        ))}

      </div>

    </div>
  );
}

export default TagInput;
