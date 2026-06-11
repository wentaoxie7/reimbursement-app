import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ApprovalTasksPage } from "./pages/ApprovalTasksPage";
import { AllExpensesPage } from "./pages/AllExpensesPage";
import { ExpenseDetailPage } from "./pages/ExpenseDetailPage";
import { ExpenseFormPage } from "./pages/ExpenseFormPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { MyExpensesPage } from "./pages/MyExpensesPage";
import { SettingsPage } from "./pages/SettingsPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p>加载中…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PageGuard({ pageKey, children }: { pageKey: string; children: React.ReactNode }) {
  const { hasPageAccess } = useAuth();
  if (!hasPageAccess(pageKey)) return <p>无页面权限</p>;
  return <>{children}</>;
}

export default function App() {
  const { user, logout, hasPermission, hasPageAccess } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <Protected>
            <div className="layout">
              <nav className="nav">
                <strong>报销 · 用户端</strong>
                {hasPageAccess("USER_HOME") && (
                  <NavLink to="/" end>
                    首页
                  </NavLink>
                )}
                {hasPageAccess("USER_ALL_EXPENSES") && <NavLink to="/all-expenses">全部报销</NavLink>}
                {hasPageAccess("USER_MY_EXPENSES") && (
                  <NavLink to="/expenses" end>
                    我的报销
                  </NavLink>
                )}
                {hasPageAccess("USER_NEW_EXPENSE") && hasPermission("EXPENSE_CREATE") && <NavLink to="/expenses/new">新建</NavLink>}
                {hasPageAccess("USER_APPROVAL_TASKS") && <NavLink to="/approval-tasks">审核任务</NavLink>}
                {hasPageAccess("USER_SETTINGS") && <NavLink to="/settings">设置</NavLink>}
                <span style={{ marginLeft: "auto" }}>欢迎，{user?.full_name || user?.email}</span>
                <button type="button" className="btn btn-secondary" onClick={logout}>
                  退出
                </button>
              </nav>
              <Routes>
                <Route path="/" element={<PageGuard pageKey="USER_HOME"><HomePage /></PageGuard>} />
                <Route path="/all-expenses" element={<PageGuard pageKey="USER_ALL_EXPENSES"><AllExpensesPage /></PageGuard>} />
                <Route path="/expenses" element={<PageGuard pageKey="USER_MY_EXPENSES"><MyExpensesPage /></PageGuard>} />
                <Route path="/expenses/new" element={<PageGuard pageKey="USER_NEW_EXPENSE"><ExpenseFormPage /></PageGuard>} />
                <Route path="/expenses/:id" element={<ExpenseDetailPage />} />
                <Route path="/approval-tasks" element={<PageGuard pageKey="USER_APPROVAL_TASKS"><ApprovalTasksPage /></PageGuard>} />
                <Route path="/settings" element={<PageGuard pageKey="USER_SETTINGS"><SettingsPage /></PageGuard>} />
              </Routes>
            </div>
          </Protected>
        }
      />
    </Routes>
  );
}
