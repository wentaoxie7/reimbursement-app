import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("employee@demo.com");
  const [password, setPassword] = useState("employee123");
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("登录失败，请检查账号密码");
    }
  };

  return (
    <div className="login-page card">
      <h1>用户系统登录</h1>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label>邮箱</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </div>
        <div className="form-group">
          <label>密码</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </div>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button className="btn btn-primary" type="submit">
          登录
        </button>
      </form>
      <p style={{ fontSize: "0.8rem", marginTop: "1rem", color: "#666" }}>
        演示：employee@demo.com / employee123 · finance@demo.com / finance123 · director@demo.com / director123
      </p>
    </div>
  );
}
