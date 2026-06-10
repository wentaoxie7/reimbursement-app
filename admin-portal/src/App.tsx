import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ApprovalSequencePage } from "./pages/ApprovalSequencePage";
import { DashboardPage } from "./pages/DashboardPage";
import { FieldConfigPage } from "./pages/FieldConfigPage";
import { LoginPage } from "./pages/LoginPage";
import { PageAccessConfigPage } from "./pages/PageAccessPage";
import { UserPermissionPage } from "./pages/UserPermissionPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading, hasPageAccess } = useAuth();
  if (loading) return <p>加载中…</p>;
  if (!user) return <Navigate to="/login" replace />;
  const canAdmin =
    hasPageAccess("ADMIN_DASHBOARD") ||
    hasPageAccess("ADMIN_FIELDS") ||
    hasPageAccess("ADMIN_USERS") ||
    hasPageAccess("ADMIN_APPROVAL") ||
    hasPageAccess("ADMIN_PAGE_ACCESS");
  if (!canAdmin) return <p>无管理权限</p>;
  return <>{children}</>;
}

function PageGuard({ pageKey, children }: { pageKey: string; children: React.ReactNode }) {
  const { hasPageAccess } = useAuth();
  if (!hasPageAccess(pageKey)) return <p>无页面权限</p>;
  return <>{children}</>;
}

export default function App() {
  const { user, logout, hasPageAccess } = useAuth();

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
                {hasPageAccess("ADMIN_DASHBOARD") && (
                  <NavLink to="/" end>
                    控制台
                  </NavLink>
                )}
                {hasPageAccess("ADMIN_FIELDS") && <NavLink to="/fields">字段</NavLink>}
                {hasPageAccess("ADMIN_USERS") && <NavLink to="/users">用户权限</NavLink>}
                {hasPageAccess("ADMIN_APPROVAL") && <NavLink to="/approval">审核顺序</NavLink>}
                {hasPageAccess("ADMIN_PAGE_ACCESS") && <NavLink to="/page-access">页面权限</NavLink>}
                <span style={{ marginLeft: "auto" }}>{user?.email}</span>
                <button type="button" className="btn btn-secondary" onClick={logout}>
                  退出
                </button>
              </nav>
              <Routes>
                <Route path="/" element={<PageGuard pageKey="ADMIN_DASHBOARD"><DashboardPage /></PageGuard>} />
                <Route path="/fields" element={<PageGuard pageKey="ADMIN_FIELDS"><FieldConfigPage /></PageGuard>} />
                <Route path="/users" element={<PageGuard pageKey="ADMIN_USERS"><UserPermissionPage /></PageGuard>} />
                <Route path="/approval" element={<PageGuard pageKey="ADMIN_APPROVAL"><ApprovalSequencePage /></PageGuard>} />
                <Route path="/page-access" element={<PageGuard pageKey="ADMIN_PAGE_ACCESS"><PageAccessConfigPage /></PageGuard>} />
              </Routes>
            </div>
          </Protected>
        }
      />
    </Routes>
  );
}
