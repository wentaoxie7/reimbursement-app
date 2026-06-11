import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Expense, type FieldDef, type FieldSchema } from "../api/client";

export function ApprovalTasksPage() {
  const [tasks, setTasks] = useState<Expense[]>([]);
  const [listFields, setListFields] = useState<FieldDef[]>([]);
  const [comments, setComments] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const load = () =>
    Promise.all([
      api.get<Expense[]>("/user/approval-tasks"),
      api.get<FieldSchema>("/user/field-schema"),
    ]).then(([tasksRes, schemaRes]) => {
      setTasks(tasksRes.data);
      setListFields(schemaRes.data.list_fields);
    });

  useEffect(() => {
    load();
  }, []);

  const getComment = (id: string) => comments[id]?.trim() ?? "";

  const updateComment = (id: string, value: string) => {
    setComments((current) => ({ ...current, [id]: value }));
  };

  const approve = async (id: string) => {
    const comment = getComment(id);
    if (!comment) {
      setError("请先填写审核记录");
      return;
    }
    setError("");
    await api.post(`/user/approval-tasks/${id}/approve`, { comment });
    setComments((current) => ({ ...current, [id]: "" }));
    load();
  };

  const reject = async (id: string) => {
    const comment = getComment(id);
    if (!comment) {
      setError("请先填写审核记录");
      return;
    }
    setError("");
    await api.post(`/user/approval-tasks/${id}/reject`, { comment });
    setComments((current) => ({ ...current, [id]: "" }));
    load();
  };

  return (
    <div className="card">
      <h1>我的审核任务</h1>
      {tasks.length === 0 ? (
        <p>暂无待审报销</p>
      ) : (
        <>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <table>
          <thead>
            <tr>
              <th>提交人</th>
              <th>Expense Type</th>
              {listFields.map((field) => (
                <th key={field.field_key}>{field.label}</th>
              ))}
              <th>审核记录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>{t.owner_name ?? t.owner_id.slice(0, 8)}</td>
                <td>{t.expense_type_name ?? "-"}</td>
                {listFields.map((field) => (
                  <td key={field.field_key}>{String(t.field_values[field.field_key] ?? "-")}</td>
                ))}
                <td style={{ minWidth: "16rem" }}>
                  <textarea
                    value={comments[t.id] ?? ""}
                    onChange={(e) => updateComment(t.id, e.target.value)}
                    placeholder="填写本次通过或退回的记录"
                    rows={3}
                  />
                </td>
                <td>
                  <Link to={`/expenses/${t.id}`} state={{ returnTo: "/approval-tasks" }}>
                    详情
                  </Link>{" "}
                  <button className="btn btn-primary" type="button" onClick={() => approve(t.id)}>
                    通过
                  </button>{" "}
                  <button className="btn btn-secondary" type="button" onClick={() => reject(t.id)}>
                    退回
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </>
      )}
    </div>
  );
}
