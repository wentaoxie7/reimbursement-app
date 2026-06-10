import type { FieldDef } from "../api/client";

type Props = {
  fields: FieldDef[];
  values: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
};

export function DynamicFieldForm({ fields, values, onChange }: Props) {
  const sorted = [...fields].sort((a, b) => a.display_order - b.display_order);

  return (
    <>
      {sorted.map((f) => (
        <div key={f.field_key} className="form-group">
          <label>
            {f.label}
            {f.required ? " *" : ""}
          </label>
          {f.field_type === "SELECT" ? (
            <select
              value={String(values[f.field_key] ?? "")}
              onChange={(e) => onChange(f.field_key, e.target.value)}
              required={f.required}
            >
              <option value="">请选择</option>
              {(f.options?.choices ?? []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          ) : f.field_type === "TEXT" ? (
            <textarea
              rows={3}
              value={String(values[f.field_key] ?? "")}
              onChange={(e) => onChange(f.field_key, e.target.value)}
              required={f.required}
            />
          ) : (
            <input
              type={f.field_type === "DATE" ? "date" : f.field_type === "NUMBER" || f.field_type === "CURRENCY" ? "number" : "text"}
              value={String(values[f.field_key] ?? "")}
              onChange={(e) =>
                onChange(
                  f.field_key,
                  f.field_type === "NUMBER" || f.field_type === "CURRENCY"
                    ? Number(e.target.value)
                    : e.target.value
                )
              }
              required={f.required}
            />
          )}
        </div>
      ))}
    </>
  );
}
