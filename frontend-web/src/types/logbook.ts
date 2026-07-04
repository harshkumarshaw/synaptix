export interface LogbookEntry {
  id: string;
  student_id: string;
  subject_code: string | null;
  elective_id: string | null;
  professional_phase: string;
  competency_code: string;
  nmc_level: "K" | "KH" | "SH" | "P";
  is_core: boolean;
  activity_date: string;
  activity_name: string;
  reflection: string | null;
  rating: "B" | "M" | "E" | null;
  faculty_decision: "C" | "R" | "Re" | null;
  faculty_initials: string | null;
  student_initials: string | null;
  status: "pending" | "submitted" | "approved" | "rejected";
  backdated: boolean;
  signed_off_by: string | null;
  signed_off_at: string | null;
  created_at: string;
}

export interface LogbookEntryCreate {
  subject_code?: string;
  elective_id?: string;
  professional_phase: string;
  competency_code: string;
  nmc_level: string;
  is_core: boolean;
  activity_date: string;
  activity_name: string;
  reflection?: string;
}

export interface LogbookSignoff {
  rating: "B" | "M" | "E";
  faculty_decision: "C" | "R" | "Re";
  faculty_initials: string;
  feedback?: string;
}

export interface LogbookSubmit {
  student_initials: string;
}

export interface IAAssessment {
  student_id: string;
  subject_code: string;
  professional_phase: string;
  total_entries: number;
  completed_entries: number;
  ia_marks_pct: number;
  ia_marks_awarded: number;
  is_complete: boolean;
}
