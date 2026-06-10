import { useEffect, useState } from "react";
import { api, type Role, type UserRow } from "../api/client";

export function UserPermissionPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [draftRoleIds, setDraftRoleIds] = useState<Record<string, string[]>>({});
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [msg, setMsg] = useState("");

  const load = async () => {
    const [{ data: roleRows }, { data: userRows }] = await Promise.all([
      api.get<Role[]>("/admin/roles"),
      api.get<UserRow[]>("/admin/users"),
    ]);
    const roleIdByCode = new Map(roleRows.map((role) => [role.code, role.id]));
    const drafts = Object.fromEntries(
      userRows.map((user) => [
        user.id,
        user.role_codes
          .map((code) => roleIdByCode.get(code))
          .filter((roleId): roleId is string => Boolean(roleId)),
      ])
    );
    setRoles(roleRows);
    setUsers(userRows);
    setDraftRoleIds(drafts);
  };

  useEffect(() => {
    load();
  }, []);

  const toggleRole = (userId: string, roleId: string) => {
    setDraftRoleIds((current) => {
      const userRoleIds = current[userId] ?? [];
      const nextRoleIds = userRoleIds.includes(roleId)
        ? userRoleIds.filter((id) => id !== roleId)
        : [...userRoleIds, roleId];
      return { ...current, [userId]: nextRoleIds };
    });
  };

  const saveRoles = async (user: UserRow) => {
    setSavingUserId(user.id);
    setMsg("");
    try {
      await api.put(`/admin/users/${user.id}/roles`, {
        role_ids: draftRoleIds[user.id] ?? [],
      });
      setMsg(`已更新 ${user.email} 的角色`);
      await load();
    } finally {
      setSavingUserId(null);
    }
  };

  return (
    <div className="card">
      <h1>用户与权限</h1>
      <table>
        <thead>
          <tr>
            <th>姓名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.full_name}</td>
              <td>{user.email}</td>
              <td>
                <div style={{ display: "grid", gap: "0.35rem" }}>
                  {roles.map((role) => (
                    <label key={role.id} style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <input
                        type="checkbox"
                        checked={(draftRoleIds[user.id] ?? []).includes(role.id)}
                        onChange={() => toggleRole(user.id, role.id)}
                      />
                      <span>{role.code}</span>
                    </label>
                  ))}
                </div>
              </td>
              <td>{user.active ? "启用" : "停用"}</td>
              <td>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => saveRoles(user)}
                  disabled={savingUserId === user.id}
                >
                  {savingUserId === user.id ? "保存中" : "保存"}
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
