import { FormEvent, useEffect, useState } from "react";
import { api, type ExpenseType, type FieldDefinition } from "../api/client";

type TabKey = "types" | "fields";
type FieldScope = "global" | "typed";

export function FieldConfigPage() {
  const [tab, setTab] = useState<TabKey>("types");
  const [fieldScope, setFieldScope] = useState<FieldScope>("global");
  const [expenseTypes, setExpenseTypes] = useState<ExpenseType[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState("");
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [typeCode, setTypeCode] = useState("");
  const [typeName, setTypeName] = useState("");
  const [key, setKey] = useState("");
  const [label, setLabel] = useState("");
  const [fieldType, setFieldType] = useState("TEXT");
  const [required, setRequired] = useState(false);
  const [showInLists, setShowInLists] = useState(false);
  const [msg, setMsg] = useState("");

  const sortExpenseTypes = (items: ExpenseType[]) =>
  [...items].sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name));

  const loadExpenseTypes = async () => {
    const { data } = await api.get<ExpenseType[]>("/admin/expense-types");
    const sorted = sortExpenseTypes(data);
    setExpenseTypes(sorted);
    setSelectedTypeId((current) => {
      if (current && sorted.some((item) => item.id === current)) return current;
      return sorted[0]?.id ?? "";
    });
    return sorted;
  };

  const loadFields = async (scope = fieldScope, expenseTypeId = selectedTypeId) => {
    if (scope === "typed" && !expenseTypeId) {
      setFields([]);
      return;
    }
    const { data } = await api.get<FieldDefinition[]>("/admin/fields", {
      params:
        scope === "global"
          ? { is_global: true }
          : { is_global: false, expense_type_id: expenseTypeId },
    });
    setFields(data);
  };

  useEffect(() => {
    loadExpenseTypes();
  }, []);

  useEffect(() => {
    loadFields(fieldScope, selectedTypeId);
  }, [fieldScope, selectedTypeId]);

  const addExpenseType = async (e: FormEvent) => {
    e.preventDefault();
    const { data } = await api.post<ExpenseType>("/admin/expense-types", {
      code: typeCode,
      name: typeName,
      display_order: expenseTypes.length,
    });
    setTypeCode("");
    setTypeName("");
    setSelectedTypeId(data.id);
    setMsg(`已添加种类：${data.name}`);
    await loadExpenseTypes();
  };

  const deleteExpenseType = async (expenseType: ExpenseType) => {
    if (!window.confirm(`删除报销种类 ${expenseType.name}？`)) return;
    try {
      await api.delete(`/admin/expense-types/${expenseType.id}`);
      setMsg(`已删除种类：${expenseType.name}`);
      const next = await loadExpenseTypes();
      if (!next.some((item) => item.id === selectedTypeId)) {
        setFields([]);
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg(typeof detail === "string" ? detail : "删除失败");
    }
  };

  const updateExpenseType = async (
    expenseType: ExpenseType,
    patch: Partial<Pick<ExpenseType, "display_order" | "code" | "name">>
  ) => {
    try {
      const { data } = await api.put<ExpenseType>(`/admin/expense-types/${expenseType.id}`, patch);
      setExpenseTypes((current) =>
        sortExpenseTypes(current.map((item) => (item.id === expenseType.id ? data : item)))
      );
      setMsg("Expense 种类已更新。发布 Schema 后用户端生效。");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg(typeof detail === "string" ? detail : "更新失败");
      loadExpenseTypes();
    }
  };
  
  const addField = async (e: FormEvent) => {
    e.preventDefault();
    if (fieldScope === "typed" && !selectedTypeId) {
      setMsg("请先创建并选择一个 Expense 种类");
      return;
    }
    await api.post("/admin/fields", {
      expense_type_id: fieldScope === "typed" ? selectedTypeId : null,
      is_global: fieldScope === "global",
      show_in_lists: fieldScope === "global" ? showInLists : false,
      field_key: key,
      label,
      field_type: fieldType,
      required,
      display_order: fields.length,
    });
    setKey("");
    setLabel("");
    setRequired(false);
    setShowInLists(false);
    setMsg("字段已添加，发布 Schema 后用户端生效。");
    loadFields(fieldScope, selectedTypeId);
  };

  const publish = async () => {
    const { data } = await api.post<{ message: string }>("/admin/fields/publish");
    setMsg(data.message);
  };

  const updateField = async (
    field: FieldDefinition,
    patch: Partial<
      Pick<
        FieldDefinition,
        "display_order" | "field_key" | "label" | "field_type" | "required" | "show_in_lists"
      >
    >
  ) => {
    try {
      const { data } = await api.put<FieldDefinition>(`/admin/fields/${field.id}`, patch);
      setFields((current) =>
        current
          .map((item) => (item.id === field.id ? data : item))
          .sort((a, b) => a.display_order - b.display_order || a.label.localeCompare(b.label))
      );
      setMsg("字段已更新。发布 Schema 后用户端生效。");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg(typeof detail === "string" ? detail : "更新失败");
      loadFields(fieldScope, selectedTypeId);
    }
  };

  const deleteField = async (field: FieldDefinition) => {
    if (!window.confirm(`删除字段 ${field.label}？`)) return;
    await api.delete(`/admin/fields/${field.id}`);
    setMsg(`已删除字段：${field.label}。发布 Schema 后用户端生效。`);
    loadFields(fieldScope, selectedTypeId);
  };

  return (
    <>
      <div className="card">
        <h1>Expense 配置</h1>
        <div className="tab-row">
          <button
            type="button"
            className={`btn ${tab === "types" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTab("types")}
          >
            Expense 种类
          </button>
          <button
            type="button"
            className={`btn ${tab === "fields" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTab("fields")}
          >
            字段配置
          </button>
        </div>
        {msg && <p>{msg}</p>}
      </div>

      {tab === "types" ? (
        <>
          <div className="card">
            <h2>新增 Expense 种类</h2>
            <form onSubmit={addExpenseType} className="row">
              <div className="form-group">
                <label>code</label>
                <input value={typeCode} onChange={(e) => setTypeCode(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>名称</label>
                <input value={typeName} onChange={(e) => setTypeName(e.target.value)} required />
              </div>
              <button type="submit" className="btn btn-primary">
                添加种类
              </button>
            </form>
          </div>
          <div className="card">
            <table>
              <thead>
                <tr>
                  <th>顺序</th>
                  <th>Code</th>
                  <th>名称</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {expenseTypes.map((expenseType) => (
                  <tr key={expenseType.id}>
                    <td>
                      <input
                        type="number"
                        defaultValue={expenseType.display_order}
                        onBlur={(e) => {
                          const displayOrder = Number(e.target.value);
                          if (Number.isFinite(displayOrder) && displayOrder !== expenseType.display_order) {
                            updateExpenseType(expenseType, { display_order: displayOrder });
                          }
                        }}
                        style={{ width: "5rem" }}
                      />
                    </td>
                    <td>
                      <input
                        defaultValue={expenseType.code}
                        onBlur={(e) => {
                          const code = e.target.value.trim();
                          if (code && code !== expenseType.code) {
                            updateExpenseType(expenseType, { code });
                          }
                        }}
                      />
                    </td>
                    <td>
                      <input
                        defaultValue={expenseType.name}
                        onBlur={(e) => {
                          const name = e.target.value.trim();
                          if (name && name !== expenseType.name) {
                            updateExpenseType(expenseType, { name });
                          }
                        }}
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => deleteExpenseType(expenseType)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <>
          <div className="card">
            <h2>字段配置</h2>
            <div className="tab-row" style={{ marginBottom: "1rem" }}>
              <button
                type="button"
                className={`btn ${fieldScope === "global" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setFieldScope("global")}
              >
                统一字段
              </button>
              <button
                type="button"
                className={`btn ${fieldScope === "typed" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setFieldScope("typed")}
              >
                按种类字段
              </button>
            </div>
            {fieldScope === "typed" && (
              <div className="form-group">
                <label>Expense 种类</label>
                <select value={selectedTypeId} onChange={(e) => setSelectedTypeId(e.target.value)}>
                  {expenseTypes.map((expenseType) => (
                    <option key={expenseType.id} value={expenseType.id}>
                      {expenseType.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {fieldScope === "typed" && !selectedTypeId ? (
              <p>请先到 “Expense 种类” tab 新建至少一个种类。</p>
            ) : (
              <>
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
                  {fieldScope === "global" && (
                    <div className="form-group">
                      <label>
                        <input
                          type="checkbox"
                          checked={showInLists}
                          onChange={(e) => setShowInLists(e.target.checked)}
                        />
                        展示在“我的报销 / 全部报销”
                      </label>
                    </div>
                  )}
                  <button type="submit" className="btn btn-primary">
                    添加字段
                  </button>
                </form>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={publish}
                  style={{ marginTop: "1rem" }}
                >
                  发布 Schema（用户端生效）
                </button>
              </>
            )}
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
                  {fieldScope === "global" && <th>列表展示</th>}
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field) => (
                  <tr key={field.id}>
                    <td>
                      <input
                        type="number"
                        defaultValue={field.display_order}
                        onBlur={(e) => {
                          const displayOrder = Number(e.target.value);
                          if (Number.isFinite(displayOrder) && displayOrder !== field.display_order) {
                            updateField(field, { display_order: displayOrder });
                          }
                        }}
                        style={{ width: "5rem" }}
                      />
                    </td>
                    <td>
                      <input
                        defaultValue={field.field_key}
                        onBlur={(e) => {
                          const fieldKey = e.target.value.trim();
                          if (fieldKey && fieldKey !== field.field_key) {
                            updateField(field, { field_key: fieldKey });
                          }
                        }}
                      />
                    </td>
                    <td>
                      <input
                        defaultValue={field.label}
                        onBlur={(e) => {
                          const nextLabel = e.target.value.trim();
                          if (nextLabel && nextLabel !== field.label) {
                            updateField(field, { label: nextLabel });
                          }
                        }}
                      />
                    </td>
                    <td>
                      <select
                        value={field.field_type}
                        onChange={(e) => updateField(field, { field_type: e.target.value })}
                      >
                        <option value="TEXT">TEXT</option>
                        <option value="NUMBER">NUMBER</option>
                        <option value="CURRENCY">CURRENCY</option>
                        <option value="DATE">DATE</option>
                        <option value="SELECT">SELECT</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={field.required}
                        onChange={(e) => updateField(field, { required: e.target.checked })}
                      />
                    </td>
                    {fieldScope === "global" && (
                      <td>
                        <input
                          type="checkbox"
                          checked={field.show_in_lists}
                          onChange={(e) => updateField(field, { show_in_lists: e.target.checked })}
                        />
                      </td>
                    )}
                    <td>
                      <button type="button" className="btn btn-secondary" onClick={() => deleteField(field)}>
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
