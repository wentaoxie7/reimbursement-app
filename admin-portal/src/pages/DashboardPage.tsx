import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function DashboardPage() {
  const { user, hasPermission } = useAuth();

  return (
    <div className="card">
      <h1>管理控制台</h1>
      <p>你好，{user?.full_name}。在此配置用户系统使用的规则。</p>
      <ul>
        {hasPermission("CONFIG_FIELDS") && (
          <li>
            <Link to="/fields">Expense 字段配置</Link>
          </li>
        )}
        {hasPermission("CONFIG_USERS") && (
          <li>
            <Link to="/users">用户与权限</Link>
          </li>
        )}
        {hasPermission("CONFIG_APPROVAL") && (
          <li>
            <Link to="/approval">审核顺序</Link>
          </li>
        )}
      </ul>
    </div>
  );
}
