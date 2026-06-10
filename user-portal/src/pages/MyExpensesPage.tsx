import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatExpenseStatus, type Expense } from "../api/client";

export function MyExpensesPage() {
  const [items, setItems] = useState<Expense[]>([]);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () =>
    api.get<Expense[]>("/user/expenses").then(({ data }) => setItems(data));

  useEffect(() => {
    load();
  }, []);

  const canWithdraw = (expense: Expense) => !["DRAFT", "ARCHIVED"].includes(expense.status);

  const removeExpense = async (expense: Expense) => {
    if (!window.confirm("删除后无法恢复，确定删除这条报销？")) return;
    setMsg("");
    setError("");
    try {
      await api.delete(`/user/expenses/${expense.id}`);
      setMsg("报销单已删除");
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "删除失败");
    }
  };

  const withdraw = async (expense: Expense) => {
    if (!window.confirm("撤回后报销单会回到草稿状态，确定撤回？")) return;
    setMsg("");
    setError("");
    try {
      await api.post(`/user/expenses/${expense.id}/withdraw`);
      setMsg("已撤回，报销单已回到草稿状态");
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "撤回失败");
    }
  };

  return (
    <div className="card">
      <h1>我的报销</h1>
      <p>
        <Link to="/expenses/new">+ 新建</Link>
      </p>
      {msg && <p>{msg}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>状态</th>
            <th>最新记录</th>
            <th>金额</th>
            <th>类别</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id}>
              <td>{e.id.slice(0, 8)}…</td>
              <td>
                <span className="badge">{formatExpenseStatus(e)}</span>
              </td>
              <td>
                {e.last_action_comment
                  ? `${e.last_action_actor_name ?? "审核人"}: ${e.last_action_comment}`
                  : "-"}
              </td>
              <td>{String(e.field_values.amount ?? "-")}</td>
              <td>{String(e.field_values.category ?? "-")}</td>
              <td>
                <Link to={`/expenses/${e.id}`}>详情</Link>{" "}
                {canWithdraw(e) && (
                  <button type="button" className="btn btn-secondary" onClick={() => withdraw(e)}>
                    撤回
                  </button>
                )}{" "}
                <button type="button" className="btn btn-secondary" onClick={() => removeExpense(e)}>
                  删除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
