import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Expense, type FieldDef, type FieldSchema } from "../api/client";
import { DynamicFieldForm } from "../components/DynamicFieldForm";

function keepMatchingValues(fields: FieldDef[], current: Record<string, unknown>) {
  const allowed = new Set(fields.map((field) => field.field_key));
  return Object.fromEntries(Object.entries(current).filter(([key]) => allowed.has(key)));
}

export function ExpenseFormPage() {
  const navigate = useNavigate();
  const [expenseTypes, setExpenseTypes] = useState<FieldSchema["expense_types"]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState("");
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [expenseId, setExpenseId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const loadSchema = async (expenseTypeId?: string) => {
    const { data } = await api.get<FieldSchema>("/user/field-schema", {
      params: expenseTypeId ? { expense_type_id: expenseTypeId } : undefined,
    });
    setExpenseTypes(data.expense_types);
    setSelectedTypeId(data.selected_expense_type_id ?? "");
    setFields(data.fields);
    setValues((current) => keepMatchingValues(data.fields, current));
  };

  useEffect(() => {
    loadSchema();
  }, []);

  useEffect(() => {
    if (!selectedTypeId) return;
    loadSchema(selectedTypeId);
  }, [selectedTypeId]);

  const onChange = (key: string, value: unknown) => setValues((v) => ({ ...v, [key]: value }));

  const saveDraft = async () => {
    setError("");
    if (!selectedTypeId) {
      setError("请先选择 Expense 种类");
      return;
    }
    if (expenseId) {
      await api.put(`/user/expenses/${expenseId}`, {
        expense_type_id: selectedTypeId,
        field_values: values,
      });
    } else {
      const { data } = await api.post<Expense>("/user/expenses", {
        expense_type_id: selectedTypeId,
        field_values: values,
      });
      setExpenseId(data.id);
    }
    navigate("/expenses");
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!selectedTypeId) {
      setError("请先选择 Expense 种类");
      return;
    }
    try {
      let id = expenseId;
      if (!id) {
        const { data } = await api.post<Expense>("/user/expenses", {
          expense_type_id: selectedTypeId,
          field_values: values,
        });
        id = data.id;
      } else {
        await api.put(`/user/expenses/${id}`, {
          expense_type_id: selectedTypeId,
          field_values: values,
        });
      }
      await api.post(`/user/expenses/${id}/submit`);
      navigate("/expenses");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "提交失败");
    }
  };

  return (
    <div className="card">
      <h1>新建报销</h1>
      <form onSubmit={submit}>
        <div className="form-group">
          <label>Expense 种类</label>
          <select value={selectedTypeId} onChange={(e) => setSelectedTypeId(e.target.value)} required>
            <option value="">请选择</option>
            {expenseTypes.map((expenseType) => (
              <option key={expenseType.id} value={expenseType.id}>
                {expenseType.name}
              </option>
            ))}
          </select>
        </div>
        <DynamicFieldForm fields={fields} values={values} onChange={onChange} />
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" className="btn btn-secondary" onClick={saveDraft}>
            保存草稿
          </button>
          <button type="submit" className="btn btn-primary">
            提交财务审核
          </button>
        </div>
      </form>
    </div>
  );
}
