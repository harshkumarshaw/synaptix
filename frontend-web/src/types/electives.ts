export interface Elective {
  id: string;
  curriculum_id: string;
  code: string;
  title: string;
  block: "Block 1" | "Block 2";
  elective_type: string;
  capacity: number;
  allocated_count: number;
}

export interface ElectivePreference {
  elective_id: string;
  rank_position: number;
}

export interface ElectiveAllocation {
  student_id: string;
  student_name: string;
  elective_id: string;
  elective_title: string;
  block: string;
  allocation_method: string;
}

export interface AllocationRunRequest {
  curriculum_id: string;
  block: "Block 1" | "Block 2";
  algorithm: "fcfs" | "ranked";
  dry_run: boolean;
  force_reallocate?: "additive" | "full" | null;
}

export interface AllocationRunResult {
  run_id: string | null;
  tenant_id: string;
  curriculum_id: string;
  block: string;
  algorithm_used: string;
  dry_run: boolean;
  force_reallocate: string | null;
  total_students_considered: number;
  total_allocated: number;
  total_unallocated_pending_review: number;
  allocations_by_rank: Record<string, number>;
  duration_ms: number | null;
  triggered_at: string;
}
