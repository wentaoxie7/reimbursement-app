import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, formatExpenseStatus, type Expense, type FieldDef, type FieldSchema } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { DynamicFieldForm } from "../components/DynamicFieldForm";

function keepMatchingValues(fields: FieldDef[], current: Record<string, unknown>) {
  const allowed = new Set(fields.map((field) => field.field_key));
  return Object.fromEntries(Object.entries(current).filter(([key]) => allowed.has(key)));
}

export function ExpenseDetailPage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();
  const [expense, setExpense] = useState<Expense | null>(null);
  const [expenseTypes, setExpenseTypes] = useState<FieldSchema["expense_types"]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState("");
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");
  const location = useLocation();
  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? "/expenses";

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
    if (!id) return;
    api.get<Expense>(`/user/expenses/${id}`).then(({ data }) => {
      setExpense(data);
      setSelectedTypeId(data.expense_type_id ?? "");
      setValues(data.field_values);
      loadSchema(data.expense_type_id ?? undefined);
    });
  }, [id]);

  useEffect(() => {
    if (!expense || !selectedTypeId || selectedTypeId === expense.expense_type_id) return;
    loadSchema(selectedTypeId);
  }, [expense, selectedTypeId]);

  const resubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setError("");
    try {
      await api.put(`/user/expenses/${id}`, {
        expense_type_id: selectedTypeId,
        field_values: values,
      });
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
      setSelectedTypeId(data.expense_type_id ?? "");
      setValues(data.field_values);
      loadSchema(data.expense_type_id ?? undefined);
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
        Expense 种类：<strong>{expenseTypes.find((item) => item.id === selectedTypeId)?.name ?? expense.expense_type_name ?? "-"}</strong>
      </p>
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
