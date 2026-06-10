import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("登录失败");
    }
  };

  return (
    <div className="login-page card">
      <h1>管理系统登录</h1>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label>邮箱</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>密码</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" className="btn btn-primary">
          登录
        </button>
      </form>
      <p style={{ fontSize: "0.8rem", color: "#666" }}>演示：admin@demo.com / admin123</p>
    </div>
  );
}
