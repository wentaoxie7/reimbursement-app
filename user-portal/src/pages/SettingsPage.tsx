import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [profileMsg, setProfileMsg] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setFullName(user?.full_name ?? "");
  }, [user?.full_name]);

  const saveProfile = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setProfileMsg("");
    const name = fullName.trim();
    if (!name) {
      setError("名称不能为空");
      return;
    }
    await api.put("/auth/me", { full_name: name });
    await refreshUser();
    setProfileMsg("名称已更新");
  };

  const savePassword = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setPasswordMsg("");
    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }
    try {
      await api.put("/auth/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMsg("密码已更新");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "密码更新失败");
    }
  };

  return (
    <div className="card">
      <h1>设置</h1>
      <form onSubmit={saveProfile}>
        <div className="form-group">
          <label>我的名称</label>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <button type="submit" className="btn btn-primary">
          保存名称
        </button>
        {profileMsg && <p>{profileMsg}</p>}
      </form>

      <hr style={{ border: 0, borderTop: "1px solid #eee", margin: "1.5rem 0" }} />

      <form onSubmit={savePassword}>
        <div className="form-group">
          <label>当前密码</label>
          <input
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            type="password"
            required
          />
        </div>
        <div className="form-group">
          <label>新密码</label>
          <input value={newPassword} onChange={(e) => setNewPassword(e.target.value)} type="password" required />
        </div>
        <div className="form-group">
          <label>确认新密码</label>
          <input
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            type="password"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">
          修改密码
        </button>
        {passwordMsg && <p>{passwordMsg}</p>}
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
