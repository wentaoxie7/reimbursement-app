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
  expense_type_id?: string | null;
  is_global: boolean;
  show_in_lists: boolean;
  options?: { choices?: string[] } | null;
  field_key: string;
  label: string;
  field_type: string;
  required: boolean;
  display_order: number;
  enabled: boolean;
};

export type ExpenseType = {
  id: string;
  code: string;
  name: string;
  active: boolean;
  display_order: number;
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
