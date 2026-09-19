export interface TopicSelection {
  topic_id: number;
  self_assessment: 'beginner' | 'intermediate' | 'advanced';
}

export interface AcademicInfo {
  college_year: string;
  stream: string;
}

export interface OnboardingPayload {
  topic_selections: TopicSelection[];
  academic_info: AcademicInfo;
  goal?: string;
  timezone: string;
}

export interface OnboardingResponse {
  success: boolean;
  message: string;
  student_id: string;
  topics_count: number;
}

export interface TopicOut {
  id: number;
  name: string;
  current_level: number | null;
}
