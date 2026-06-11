import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatExpenseStatus, type Expense, type FieldDef, type FieldSchema } from "../api/client";

export function AllExpensesPage() {
  const [items, setItems] = useState<Expense[]>([]);
  const [listFields, setListFields] = useState<FieldDef[]>([]);

  useEffect(() => {
    Promise.all([
      api.get<Expense[]>("/user/all-expenses"),
      api.get<FieldSchema>("/user/field-schema"),
    ]).then(([expensesRes, schemaRes]) => {
      setItems(expensesRes.data);
      setListFields(schemaRes.data.list_fields);
    });
  }, []);

  return (
    <div className="card">
      <h1>全部报销</h1>
      <table>
        <thead>
          <tr>
            <th>提交人</th>
            <th>Expense Type</th>
            {listFields.map((field) => (
              <th key={field.field_key}>{field.label}</th>
            ))}
            <th>状态</th>
            <th>最新记录</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((expense) => (
            <tr key={expense.id}>
              <td>{expense.owner_name ?? expense.owner_id.slice(0, 8)}</td>
              <td>{expense.expense_type_name ?? "-"}</td>
              {listFields.map((field) => (
                <td key={field.field_key}>{String(expense.field_values[field.field_key] ?? "-")}</td>
              ))}
              <td>
                <span className="badge">{formatExpenseStatus(expense)}</span>
              </td>
              <td>
                {expense.last_action_comment
                  ? `${expense.last_action_actor_name ?? "审核人"}: ${expense.last_action_comment}`
                  : "-"}
              </td>
              <td>
                <Link to={`/expenses/${expense.id}`} state={{ returnTo: "/all-expenses" }}>
                  详情
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
