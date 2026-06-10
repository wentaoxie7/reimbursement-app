import { FormEvent, useEffect, useState } from "react";
import { api, type FieldDefinition } from "../api/client";

export function FieldConfigPage() {
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [key, setKey] = useState("");
  const [label, setLabel] = useState("");
  const [fieldType, setFieldType] = useState("TEXT");
  const [required, setRequired] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => api.get<FieldDefinition[]>("/admin/fields").then(({ data }) => setFields(data));

  useEffect(() => {
    load();
  }, []);

  const addField = async (e: FormEvent) => {
    e.preventDefault();
    await api.post("/admin/fields", {
      field_key: key,
      label,
      field_type: fieldType,
      required,
      display_order: fields.length,
    });
    setKey("");
    setLabel("");
    setRequired(false);
    load();
  };

  const publish = async () => {
    const { data } = await api.post<{ message: string }>("/admin/fields/publish");
    setMsg(data.message);
  };

  const deleteField = async (field: FieldDefinition) => {
    if (!window.confirm(`删除字段 ${field.label}？`)) return;
    await api.delete(`/admin/fields/${field.id}`);
    setMsg(`已删除字段：${field.label}。发布 Schema 后用户端生效。`);
    load();
  };

  return (
    <>
      <div className="card">
        <h1>Expense 字段配置</h1>
        <form onSubmit={addField} className="row">
          <div className="form-group">
            <label>field_key</label>
            <input value={key} onChange={(e) => setKey(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>显示名</label>
            <input value={label} onChange={(e) => setLabel(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>类型</label>
            <select value={fieldType} onChange={(e) => setFieldType(e.target.value)}>
              <option value="TEXT">TEXT</option>
              <option value="NUMBER">NUMBER</option>
              <option value="CURRENCY">CURRENCY</option>
              <option value="DATE">DATE</option>
              <option value="SELECT">SELECT</option>
            </select>
          </div>
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={required}
                onChange={(e) => setRequired(e.target.checked)}
              />
              必填
            </label>
          </div>
          <button type="submit" className="btn btn-primary">
            添加字段
          </button>
        </form>
        <button type="button" className="btn btn-secondary" onClick={publish} style={{ marginTop: "1rem" }}>
          发布 Schema（用户端生效）
        </button>
        {msg && <p>{msg}</p>}
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>顺序</th>
              <th>Key</th>
              <th>标签</th>
              <th>类型</th>
              <th>必填</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((f) => (
              <tr key={f.id}>
                <td>{f.display_order}</td>
                <td>{f.field_key}</td>
                <td>{f.label}</td>
                <td>{f.field_type}</td>
                <td>{f.required ? "是" : "否"}</td>
                <td>
                  <button type="button" className="btn btn-secondary" onClick={() => deleteField(f)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
