import { FormEvent, useEffect, useState } from "react";
import { api, type ExpenseType, type FieldDefinition } from "../api/client";

type TabKey = "types" | "fields";

export function FieldConfigPage() {
  const [tab, setTab] = useState<TabKey>("types");
  const [expenseTypes, setExpenseTypes] = useState<ExpenseType[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState("");
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [typeCode, setTypeCode] = useState("");
  const [typeName, setTypeName] = useState("");
  const [key, setKey] = useState("");
  const [label, setLabel] = useState("");
  const [fieldType, setFieldType] = useState("TEXT");
  const [required, setRequired] = useState(false);
  const [msg, setMsg] = useState("");

  const loadExpenseTypes = async () => {
    const { data } = await api.get<ExpenseType[]>("/admin/expense-types");
    setExpenseTypes(data);
    setSelectedTypeId((current) => {
      if (current && data.some((item) => item.id === current)) return current;
      return data[0]?.id ?? "";
    });
    return data;
  };

  const loadFields = async (expenseTypeId: string) => {
    if (!expenseTypeId) {
      setFields([]);
      return;
    }
    const { data } = await api.get<FieldDefinition[]>("/admin/fields", {
      params: { expense_type_id: expenseTypeId },
    });
    setFields(data);
  };

  useEffect(() => {
    loadExpenseTypes();
  }, []);

  useEffect(() => {
    loadFields(selectedTypeId);
  }, [selectedTypeId]);

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

  const addField = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedTypeId) {
      setMsg("请先创建并选择一个 Expense 种类");
      return;
    }
    await api.post("/admin/fields", {
      expense_type_id: selectedTypeId,
      field_key: key,
      label,
      field_type: fieldType,
      required,
      display_order: fields.length,
    });
    setKey("");
    setLabel("");
    setRequired(false);
    setMsg("字段已添加，发布 Schema 后用户端生效。");
    loadFields(selectedTypeId);
  };

  const publish = async () => {
    const { data } = await api.post<{ message: string }>("/admin/fields/publish");
    setMsg(data.message);
  };

  const deleteField = async (field: FieldDefinition) => {
    if (!window.confirm(`删除字段 ${field.label}？`)) return;
    await api.delete(`/admin/fields/${field.id}`);
    setMsg(`已删除字段：${field.label}。发布 Schema 后用户端生效。`);
    loadFields(selectedTypeId);
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
                    <td>{expenseType.display_order}</td>
                    <td>{expenseType.code}</td>
                    <td>{expenseType.name}</td>
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
            <h2>按种类配置字段</h2>
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
            {!selectedTypeId ? (
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
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field) => (
                  <tr key={field.id}>
                    <td>{field.display_order}</td>
                    <td>{field.field_key}</td>
                    <td>{field.label}</td>
                    <td>{field.field_type}</td>
                    <td>{field.required ? "是" : "否"}</td>
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
