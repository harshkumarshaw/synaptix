export interface AttendanceSummary {
  student_id: string;
  course_id: string;
  course_name: string;
  subject_code: string;
  attendance_category: string;
  sessions_conducted: number;
  sessions_present: number;
  sessions_excused: number;
  sessions_medical: number;
  sessions_official_duty: number;
  attendance_pct: number;
  threshold: number;
  is_eligible: boolean;
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  event_id: string;
  status:
    | "present"
    | "absent"
    | "late"
    | "excused"
    | "medical"
    | "official_duty"
    | "exempt";
  method: string;
  marked_at: string;
  needs_review: boolean;
}

export interface EventRoster {
  event_id: string;
  event_date: string;
  course_name: string;
  attendance_category: string;
  students: AttendanceRecord[];
  total_students: number;
  marked_count: number;
}

export interface MarkAttendanceRequest {
  event_id: string;
  student_id: string;
  status: string;
  method?: string;
}

export interface BulkMarkRequest {
  event_id: string;
  marks: { student_id: string; status: string }[];
}

export interface ExamEligibility {
  student_id: string;
  course_id: string;
  theory_pct: number;
  practical_pct: number;
  theory_eligible: boolean;
  practical_eligible: boolean;
  theory_threshold: number;
  practical_threshold: number;
}

export interface DashboardStats {
  total_students: number;
  todays_attendance_rate: number;
  pending_logbook_reviews: number;
  at_risk_students: number;
}

export interface TodayEvent {
  id: string;
  course_name: string;
  event_type: string;
  start_time: string;
  end_time: string;
  room: string | null;
  attendance_marked: boolean;
  students_present: number;
  students_total: number;
}
