import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type FieldDefinition = {
  id: string;
  field_key: string;
  label: string;
  field_type: string;
  required: boolean;
  display_order: number;
  enabled: boolean;
};

export type UserRow = {
  id: string;
  email: string;
  full_name: string;
  active: boolean;
  role_codes: string[];
};

export type Role = {
  id: string;
  code: string;
  name: string;
};

export type PageAccessPage = {
  key: string;
  label: string;
  portal: string;
  role_codes: string[];
  role_ids: string[];
};

export type ApprovalStep = {
  id: string;
  step_order: number;
  approver_rule: string;
  fixed_user_id: string | null;
  role_code: string | null;
};

export type ApprovalSequence = {
  id: string;
  name: string;
  is_default: boolean;
  active: boolean;
  steps: ApprovalStep[];
};
