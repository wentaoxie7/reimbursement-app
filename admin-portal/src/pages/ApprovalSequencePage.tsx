import { FormEvent, useEffect, useState } from "react";
import { api, type ApprovalSequence, type Role } from "../api/client";

export function ApprovalSequencePage() {
  const [sequences, setSequences] = useState<ApprovalSequence[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [name, setName] = useState("Finance then Director");
  const [firstRoleCode, setFirstRoleCode] = useState("FINANCE");
  const [secondRoleCode, setSecondRoleCode] = useState("DIRECTOR");
  const [msg, setMsg] = useState("");

  const load = async () => {
    const [{ data: sequenceRows }, { data: roleRows }] = await Promise.all([
      api.get<ApprovalSequence[]>("/admin/approval-sequences"),
      api.get<Role[]>("/admin/roles"),
    ]);
    setSequences(sequenceRows);
    setRoles(roleRows);
  };

  useEffect(() => {
    load();
  }, []);

  const createDefault = async (e: FormEvent) => {
    e.preventDefault();
    setMsg("");
    const { data: seq } = await api.post<ApprovalSequence>("/admin/approval-sequences", {
      name,
      steps: [
        { step_order: 1, approver_rule: "ROLE", role_code: firstRoleCode },
        { step_order: 2, approver_rule: "ROLE", role_code: secondRoleCode },
      ],
    });
    await api.post(`/admin/approval-sequences/${seq.id}/default`);
    setMsg(`已创建并设为默认：${seq.name}`);
    load();
  };

  const setDefault = async (id: string) => {
    await api.post(`/admin/approval-sequences/${id}/default`);
    setMsg("已更新默认审核链");
    load();
  };

  const deleteSequence = async (sequence: ApprovalSequence) => {
    if (!window.confirm(`删除审核顺序 ${sequence.name}？`)) return;
    try {
      await api.delete(`/admin/approval-sequences/${sequence.id}`);
      setMsg(`已删除审核顺序：${sequence.name}`);
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg(typeof detail === "string" ? detail : "删除失败");
    }
  };

  return (
    <>
      <div className="card">
        <h1>审核顺序</h1>
        <form onSubmit={createDefault} className="row">
          <div className="form-group">
            <label>流程名称</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label>第 1 步角色 CODE</label>
            <select value={firstRoleCode} onChange={(e) => setFirstRoleCode(e.target.value)}>
              {roles.map((role) => (
                <option key={role.id} value={role.code}>
                  {role.code}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>第 2 步角色 CODE</label>
            <select value={secondRoleCode} onChange={(e) => setSecondRoleCode(e.target.value)}>
              {roles.map((role) => (
                <option key={role.id} value={role.code}>
                  {role.code}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary">
            创建两步流程并设为默认
          </button>
        </form>
        {msg && <p>{msg}</p>}
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th>步骤</th>
              <th>默认</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {sequences.map((sequence) => (
              <tr key={sequence.id}>
                <td>{sequence.name}</td>
                <td>
                  {[...sequence.steps]
                    .sort((a, b) => a.step_order - b.step_order)
                    .map((step) => `${step.step_order}. ${step.role_code ?? step.approver_rule}`)
                    .join(" -> ")}
                </td>
                <td>{sequence.is_default ? "是" : "否"}</td>
                <td>
                  {!sequence.is_default && (
                    <button type="button" className="btn btn-secondary" onClick={() => setDefault(sequence.id)}>
                      设为默认
                    </button>
                  )}{" "}
                  <button type="button" className="btn btn-secondary" onClick={() => deleteSequence(sequence)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
