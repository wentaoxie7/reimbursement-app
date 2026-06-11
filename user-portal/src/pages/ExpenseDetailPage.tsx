import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api, formatExpenseStatus, getApiErrorMessage, type Expense, type FieldDef, type FieldSchema } from "../api/client";
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
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState("");
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [pendingImages, setPendingImages] = useState<File[]>([]);
  const [error, setError] = useState("");
  const location = useLocation();
  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? "/expenses";

  const loadExpense = async () => {
    if (!id) return;
    const { data } = await api.get<Expense>(`/user/expenses/${id}`);
    setExpense(data);
    setSelectedTypeId(data.expense_type_id ?? "");
    setValues(data.field_values);
    await loadSchema(data.expense_type_id ?? undefined);
  };

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
    loadExpense();
  }, [id]);

  useEffect(() => {
    if (!expense || !selectedTypeId || selectedTypeId === expense.expense_type_id) return;
    loadSchema(selectedTypeId);
  }, [expense, selectedTypeId]);

  const uploadPendingImages = async () => {
    if (!id || pendingImages.length === 0) return;
    const formData = new FormData();
    pendingImages.forEach((image) => formData.append("files", image));
    const { data } = await api.post<Expense>(`/user/expenses/${id}/receipts`, formData);
    setExpense(data);
    setPendingImages([]);
  };

  const deleteReceipt = async (receiptId: string) => {
    if (!id || !window.confirm("确定删除这张图片？")) return;
    setError("");
    try {
      const { data } = await api.delete<Expense>(`/user/expenses/${id}/receipts/${receiptId}`);
      setExpense(data);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "删除图片失败"));
    }
  };

  const resubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setError("");
    try {
      await api.put(`/user/expenses/${id}`, {
        expense_type_id: selectedTypeId,
        field_values: values,
      });
      await uploadPendingImages();
      await api.post(`/user/expenses/${id}/${expense?.status === "DRAFT" ? "submit" : "resubmit"}`);
      window.location.href = "/expenses";
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "提交失败"));
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
      await loadSchema(data.expense_type_id ?? undefined);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "撤回失败"));
    }
  };

  const visibleFields = useMemo(() => {
    const schemaKeys = new Set(fields.map((field) => field.field_key));
    const extras = Object.keys(expense?.field_values ?? {})
      .filter((key) => !schemaKeys.has(key))
      .map((key, index) => ({
        field_key: key,
        label: key,
        field_type: "TEXT",
        required: false,
        display_order: fields.length + index,
      }));
    return [...fields, ...extras];
  }, [expense?.field_values, fields]);

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
          <div className="form-group">
            <label>上传图片</label>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setPendingImages(Array.from(e.target.files ?? []))}
            />
            {pendingImages.length > 0 && (
              <p style={{ marginTop: "0.5rem" }}>
                待上传：{pendingImages.map((image) => image.name).join(", ")}
              </p>
            )}
          </div>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button type="submit" className="btn btn-primary">
            {expense.status === "DRAFT" ? "修改并提交" : "修改并重新提交"}
          </button>
        </form>
      ) : (
        <div className="form-group">
          <label>Expense 信息</label>
          <table>
            <tbody>
              {visibleFields.map((field) => (
                <tr key={field.field_key}>
                  <th style={{ width: "14rem" }}>{field.label}</th>
                  <td>{String(expense.field_values[field.field_key] ?? "-")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="form-group">
        <label>图片</label>
        {expense.receipts && expense.receipts.length > 0 ? (
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {expense.receipts.map((receipt) => (
              <div key={receipt.id}>
                <a href={receipt.file_url} target="_blank" rel="noreferrer">
                  <img
                    src={receipt.file_url}
                    alt="expense receipt"
                    style={{
                      width: "180px",
                      height: "180px",
                      objectFit: "cover",
                      borderRadius: "8px",
                      border: "1px solid #d1d5db",
                      display: "block",
                    }}
                  />
                </a>
                {editable && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ marginTop: "0.5rem", width: "100%" }}
                    onClick={() => deleteReceipt(receipt.id)}
                  >
                    删除图片
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p>暂无图片</p>
        )}
      </div>
      <p>
        <Link to={returnTo}>返回列表</Link>
      </p>
    </div>
  );
}
