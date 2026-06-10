import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Expense, type FieldDef } from "../api/client";
import { DynamicFieldForm } from "../components/DynamicFieldForm";

export function ExpenseFormPage() {
  const navigate = useNavigate();
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [expenseId, setExpenseId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<{ fields: FieldDef[] }>("/user/field-schema").then(({ data }) => setFields(data.fields));
  }, []);

  const onChange = (key: string, value: unknown) => setValues((v) => ({ ...v, [key]: value }));

  const saveDraft = async () => {
    setError("");
    if (expenseId) {
      await api.put(`/user/expenses/${expenseId}`, { field_values: values });
    } else {
      const { data } = await api.post<Expense>("/user/expenses", { field_values: values });
      setExpenseId(data.id);
    }
    navigate("/expenses");
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      let id = expenseId;
      if (!id) {
        const { data } = await api.post<Expense>("/user/expenses", { field_values: values });
        id = data.id;
      } else {
        await api.put(`/user/expenses/${id}`, { field_values: values });
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
