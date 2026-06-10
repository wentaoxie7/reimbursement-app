import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatExpenseStatus, type Expense } from "../api/client";

export function AllExpensesPage() {
  const [items, setItems] = useState<Expense[]>([]);

  useEffect(() => {
    api.get<Expense[]>("/user/all-expenses").then(({ data }) => setItems(data));
  }, []);

  return (
    <div className="card">
      <h1>全部报销</h1>
      <table>
        <thead>
          <tr>
            <th>提交人</th>
            <th>ID</th>
            <th>状态</th>
            <th>最新记录</th>
            <th>金额</th>
            <th>类别</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((expense) => (
            <tr key={expense.id}>
              <td>{expense.owner_name ?? expense.owner_id.slice(0, 8)}</td>
              <td>{expense.id.slice(0, 8)}…</td>
              <td>
                <span className="badge">{formatExpenseStatus(expense)}</span>
              </td>
              <td>
                {expense.last_action_comment
                  ? `${expense.last_action_actor_name ?? "审核人"}: ${expense.last_action_comment}`
                  : "-"}
              </td>
              <td>{String(expense.field_values.amount ?? "-")}</td>
              <td>{String(expense.field_values.category ?? "-")}</td>
              <td>
                <Link to={`/expenses/${expense.id}`}>详情</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
