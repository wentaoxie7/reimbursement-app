import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ApprovalSequencePage } from "./pages/ApprovalSequencePage";
import { DashboardPage } from "./pages/DashboardPage";
import { FieldConfigPage } from "./pages/FieldConfigPage";
import { LoginPage } from "./pages/LoginPage";
import { UserPermissionPage } from "./pages/UserPermissionPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading, hasPermission } = useAuth();
  if (loading) return <p>加载中…</p>;
  if (!user) return <Navigate to="/login" replace />;
  const canAdmin =
    hasPermission("CONFIG_FIELDS") ||
    hasPermission("CONFIG_USERS") ||
    hasPermission("CONFIG_APPROVAL");
  if (!canAdmin) return <p>无管理权限</p>;
  return <>{children}</>;
}

export default function App() {
  const { user, logout } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <Protected>
            <div className="layout">
              <nav className="nav">
                <strong>报销 · 管理端</strong>
                <NavLink to="/" end>
                  控制台
                </NavLink>
                <NavLink to="/fields">字段</NavLink>
                <NavLink to="/users">用户权限</NavLink>
                <NavLink to="/approval">审核顺序</NavLink>
                <span style={{ marginLeft: "auto" }}>{user?.email}</span>
                <button type="button" className="btn btn-secondary" onClick={logout}>
                  退出
                </button>
              </nav>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/fields" element={<FieldConfigPage />} />
                <Route path="/users" element={<UserPermissionPage />} />
                <Route path="/approval" element={<ApprovalSequencePage />} />
              </Routes>
            </div>
          </Protected>
        }
      />
    </Routes>
  );
}
