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

export default function App() {
  const { user, logout, hasPermission } = useAuth();

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
                <NavLink to="/" end>
                  首页
                </NavLink>
                {hasPermission("APPROVAL_ACT") && <NavLink to="/all-expenses">全部报销</NavLink>}
                <NavLink to="/expenses">我的报销</NavLink>
                {hasPermission("EXPENSE_CREATE") && <NavLink to="/expenses/new">新建</NavLink>}
                {hasPermission("APPROVAL_ACT") && <NavLink to="/approval-tasks">审核任务</NavLink>}
                <NavLink to="/settings">设置</NavLink>
                <span style={{ marginLeft: "auto" }}>欢迎，{user?.full_name || user?.email}</span>
                <button type="button" className="btn btn-secondary" onClick={logout}>
                  退出
                </button>
              </nav>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/all-expenses" element={<AllExpensesPage />} />
                <Route path="/expenses" element={<MyExpensesPage />} />
                <Route path="/expenses/new" element={<ExpenseFormPage />} />
                <Route path="/expenses/:id" element={<ExpenseDetailPage />} />
                <Route path="/approval-tasks" element={<ApprovalTasksPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Routes>
            </div>
          </Protected>
        }
      />
    </Routes>
  );
}
