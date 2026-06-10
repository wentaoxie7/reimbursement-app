import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function HomePage() {
  const { user, hasPageAccess, hasPermission } = useAuth();

  return (
    <div className="card">
      <h1>欢迎，{user?.full_name}</h1>
      <p>用户系统：填报 Expense，按 Admin 配置的字段与审核顺序流转。</p>
      <ul>
        {hasPageAccess("USER_ALL_EXPENSES") && (
          <li>
            <Link to="/all-expenses">全部报销</Link>
          </li>
        )}
        {hasPageAccess("USER_NEW_EXPENSE") && hasPermission("EXPENSE_CREATE") && (
          <li>
            <Link to="/expenses/new">新建报销</Link>
          </li>
        )}
        {hasPageAccess("USER_MY_EXPENSES") && (
          <li>
          <Link to="/expenses">我的报销</Link>
          </li>
        )}
        {hasPageAccess("USER_APPROVAL_TASKS") && (
          <li>
            <Link to="/approval-tasks">我的审核任务</Link>
          </li>
        )}
      </ul>
    </div>
  );
}
