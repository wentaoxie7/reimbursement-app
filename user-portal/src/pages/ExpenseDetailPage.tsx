import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, formatExpenseStatus, type Expense, type FieldDef } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { DynamicFieldForm } from "../components/DynamicFieldForm";

export function ExpenseDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const [expense, setExpense] = useState<Expense | null>(null);
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");
  const location = useLocation();
  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? "/expenses";

  useEffect(() => {
    if (!id) return;
    api.get<Expense>(`/user/expenses/${id}`).then(({ data }) => {
      setExpense(data);
      setValues(data.field_values);
    });
    api.get<{ fields: FieldDef[] }>("/user/field-schema").then(({ data }) => setFields(data.fields));
  }, [id]);

  const resubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setError("");
    try {
      await api.put(`/user/expenses/${id}`, { field_values: values });
      await api.post(`/user/expenses/${id}/${expense?.status === "DRAFT" ? "submit" : "resubmit"}`);
      window.location.href = "/expenses";
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "提交失败");
    }
  };

  const withdraw = async () => {
    if (!id || !window.confirm("撤回后报销单会回到草稿状态，确定撤回？")) return;
    setError("");
    try {
      const { data } = await api.post<Expense>(`/user/expenses/${id}/withdraw`);
      setExpense(data);
      setValues(data.field_values);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "撤回失败");
    }
  };

  if (!expense) return <p>加载中…</p>;

  const isOwner = expense.owner_id === user?.id;
  const editable = isOwner && (expense.status === "REJECTED" || expense.status === "DRAFT");
  const withdrawable = isOwner && !["DRAFT", "ARCHIVED"].includes(expense.status);

  return (
    <div className="card">
      <h1>报销详情</h1>
      <p>
        状态：<span className="badge">{formatExpenseStatus(expense)}</span>
      </p>
      {expense.last_action_comment && (
        <div className="form-group">
          <label>最新审核记录</label>
          <div
            style={{
              padding: "0.9rem",
              background: "#f8fafc",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
            }}
          >
            <strong>
              {expense.last_action_actor_name ?? "审核人"}
              {expense.last_action_type ? ` · ${expense.last_action_type}` : ""}
            </strong>
            <p style={{ marginBottom: 0 }}>{expense.last_action_comment}</p>
          </div>
        </div>
      )}
      {withdrawable && (
        <p>
          <button type="button" className="btn btn-secondary" onClick={withdraw}>
            撤回到草稿
          </button>
        </p>
      )}
      {editable ? (
        <form onSubmit={resubmit}>
          <DynamicFieldForm fields={fields} values={values} onChange={(k, v) => setValues((s) => ({ ...s, [k]: v }))} />
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button type="submit" className="btn btn-primary">
            {expense.status === "DRAFT" ? "修改并提交" : "修改并重新提交"}
          </button>
        </form>
      ) : (
        <pre>{JSON.stringify(expense.field_values, null, 2)}</pre>
      )}
      <p>
        <Link to={returnTo}>返回列表</Link>
      </p>
    </div>
  );
}
