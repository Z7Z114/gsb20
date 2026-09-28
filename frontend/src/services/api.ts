import axios from 'axios'
import type { Child, TeamMember, Meeting, BehaviorRecord, BehaviorChartData, TranscriptSegment, IEPSummaryResponse, MeetingParticipant } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export const childApi = {
  getAll: () => api.get<Child[]>('/core/children'),
  getById: (id: number) => api.get<Child>(`/core/children/${id}`),
  create: (data: { name: string; age?: number; diagnosis?: string }) =>
    api.post<Child>('/core/children', data),
}

export const teamMemberApi = {
  getAll: () => api.get<TeamMember[]>('/core/team-members'),
  create: (data: { name: string; role: string; email: string }) =>
    api.post<TeamMember>('/core/team-members', data),
}

export const meetingApi = {
  getAll: (childId?: number) =>
    api.get<Meeting[]>('/core/meetings', { params: childId ? { child_id: childId } : undefined }),
  getById: (id: number) => api.get<Meeting>(`/core/meetings/${id}`),
  create: (data: { child_id: number; title: string; date?: string; participant_ids: number[] }) =>
    api.post<Meeting>('/core/meetings', data),
  getParticipants: (id: number) => api.get<MeetingParticipant[]>(`/core/meetings/${id}/participants`),
  getTranscripts: (id: number) => api.get<TranscriptSegment[]>(`/core/meetings/${id}/transcripts`),
  getStatus: (id: number) => api.get(`/processing/meeting-status/${id}`),
  uploadAudio: (id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/processing/upload-audio/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  process: (id: number) => api.post(`/processing/process-meeting/${id}`),
  sendEmail: (id: number) => api.post(`/processing/send-email/${id}`),
  getIepSummary: (id: number) => api.get<IEPSummaryResponse>(`/processing/iep-summary/${id}`),
}

export const behaviorApi = {
  getChartData: (childId: number) =>
    api.get<BehaviorChartData[]>(`/core/behavior-records/chart/${childId}`),
  getByChildId: (childId: number) =>
    api.get<BehaviorRecord[]>(`/core/behavior-records/${childId}`),
  create: (data: {
    child_id: number
    behavior_type: string
    frequency: number
    intensity?: number
    duration?: number
    notes?: string
    target_behavior?: boolean
    recorded_at?: string
  }) => api.post<BehaviorRecord>('/core/behavior-records', data),
}
