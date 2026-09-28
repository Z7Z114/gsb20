export interface Child {
  id: number
  name: string
  age?: number
  diagnosis?: string
  created_at: string
}

export interface TeamMember {
  id: number
  name: string
  role: string
  email: string
  created_at: string
}

export interface Meeting {
  id: number
  child_id: number
  title: string
  date: string
  status: string
  transcript?: string
  iep_summary?: string
  suggestions?: string
  created_at: string
}

export interface BehaviorRecord {
  id: number
  child_id: number
  behavior_type: string
  frequency: number
  intensity?: number
  duration?: number
  notes?: string
  target_behavior: boolean
  recorded_at: string
  created_at: string
}

export interface BehaviorChartData {
  date: string
  behavior_type: string
  frequency: number
  intensity?: number
}

export interface TranscriptSegment {
  id: number
  speaker: string
  speaker_role?: string
  start_time: number
  end_time: number
  text: string
}

export interface IEPSummaryResponse {
  meeting_id: number
  child_name: string
  meeting_date: string
  summary: string
  suggestions: string[]
  target_behaviors: string[]
  intervention_strategies: string[]
  progress_notes: string
}

export interface MeetingParticipant {
  id: number
  name: string
  role: string
  email: string
  role_in_meeting?: string
}
