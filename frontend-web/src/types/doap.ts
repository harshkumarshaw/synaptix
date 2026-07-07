export interface DoapRecord {
  id: string;
  student_id: string;
  competency_code: string;
  stage: "D" | "O" | "A" | "P";
  rating: "B" | "M" | "E";
  attempt_type: "F" | "R" | "Re";
  faculty_decision: "C" | "R" | "Re";
  faculty_id: string;
  signed_off_at: string;
  notes?: string;
}

export interface DoapState {
  student_id: string;
  competency_code: string;
  current_state: "not_started" | "demonstrated" | "observed" | "assisted" | "performed" | "certified";
  records_per_stage: Record<string, number>;
  certified_stages: string[];
  pending_stage: string | null;
  last_record_at: string | null;
}

export interface DoapProgression {
  student_id: string;
  competency_code: string;
  state: DoapState;
  records: DoapRecord[];
}
