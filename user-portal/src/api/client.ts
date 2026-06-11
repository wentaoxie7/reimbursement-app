import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type FieldDef = {
  field_key: string;
  label: string;
  field_type: string;
  required: boolean;
  display_order: number;
  options?: { choices?: string[] };
  is_global?: boolean;
  show_in_lists?: boolean;
};

export type ExpenseTypeOption = {
  id: string;
  code: string;
  name: string;
};

export type Receipt = {
  id: string;
  file_url: string;
  mime_type?: string | null;
};

export type FieldSchema = {
  version_id: string | null;
  version: number | null;
  expense_types: ExpenseTypeOption[];
  selected_expense_type_id: string | null;
  list_fields: FieldDef[];
  fields: FieldDef[];
};

export type Expense = {
  id: string;
  owner_id: string;
  owner_name?: string | null;
  expense_type_id?: string | null;
  expense_type_name?: string | null;
  status: string;
  field_values: Record<string, unknown>;
  current_approval_role_code?: string | null;
  current_approver_names?: string[];
  last_action_type?: string | null;
  last_action_comment?: string | null;
  last_action_actor_name?: string | null;
  receipts?: Receipt[];
  submitted_at: string | null;
  created_at: string;
};

export function formatExpenseStatus(expense: Expense) {
  const names = expense.current_approver_names ?? [];
  if (expense.status === "IN_APPROVAL" && names.length > 0) {
    return `${expense.status}: ${names.join(", ")}`;
  }
  if (expense.status === "IN_APPROVAL" && expense.current_approval_role_code) {
    return `${expense.status}: ${expense.current_approval_role_code}`;
  }
  return expense.status;
}
