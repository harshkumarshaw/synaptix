export interface LeaveRequest {
  id: string;
  student_id: string;
  student_name: string;
  leave_type: "medical" | "academic" | "casual" | "other";
  start_date: string;
  end_date: string;
  reason: string;
  status: "pending" | "approved" | "rejected" | "cancelled";
  workflow_instance_id: string | null;
  created_at: string;
}

export interface LeaveRequestCreate {
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string;
}
