import { useEffect, useState } from "react";
import { api, type PageAccessPage, type Role } from "../api/client";

export function PageAccessConfigPage() {
  const [pages, setPages] = useState<PageAccessPage[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [draftRoleIds, setDraftRoleIds] = useState<Record<string, string[]>>({});
  const [savingPageKey, setSavingPageKey] = useState<string | null>(null);
  const [msg, setMsg] = useState("");

  const load = async () => {
    const [{ data: pageRows }, { data: roleRows }] = await Promise.all([
      api.get<PageAccessPage[]>("/admin/page-access"),
      api.get<Role[]>("/admin/roles"),
    ]);
    setPages(pageRows);
    setRoles(roleRows);
    setDraftRoleIds(Object.fromEntries(pageRows.map((page) => [page.key, page.role_ids])));
  };

  useEffect(() => {
    load();
  }, []);

  const toggleRole = (pageKey: string, roleId: string) => {
    setDraftRoleIds((current) => {
      const roleIds = current[pageKey] ?? [];
      const nextRoleIds = roleIds.includes(roleId)
        ? roleIds.filter((id) => id !== roleId)
        : [...roleIds, roleId];
      return { ...current, [pageKey]: nextRoleIds };
    });
  };

  const savePageAccess = async (page: PageAccessPage) => {
    setSavingPageKey(page.key);
    setMsg("");
    try {
      await api.put(`/admin/page-access/${page.key}`, { role_ids: draftRoleIds[page.key] ?? [] });
      setMsg(`已更新页面权限：${page.label}`);
      await load();
    } finally {
      setSavingPageKey(null);
    }
  };

  return (
    <div className="card">
      <h1>页面权限</h1>
      <table>
        <thead>
          <tr>
            <th>端</th>
            <th>页面</th>
            <th>可访问角色</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {pages.map((page) => (
            <tr key={page.key}>
              <td>{page.portal === "admin" ? "管理端" : "用户端"}</td>
              <td>{page.label}</td>
              <td>
                <div style={{ display: "grid", gap: "0.35rem" }}>
                  {roles.map((role) => (
                    <label key={role.id} style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <input
                        type="checkbox"
                        checked={(draftRoleIds[page.key] ?? []).includes(role.id)}
                        onChange={() => toggleRole(page.key, role.id)}
                      />
                      <span>{role.code}</span>
                    </label>
                  ))}
                </div>
              </td>
              <td>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => savePageAccess(page)}
                  disabled={savingPageKey === page.key}
                >
                  {savingPageKey === page.key ? "保存中" : "保存"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {msg && <p>{msg}</p>}
    </div>
  );
}
