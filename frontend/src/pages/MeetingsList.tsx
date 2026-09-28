import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { meetingApi, childApi, teamMemberApi } from '../services/api'
import type { Meeting, Child, TeamMember } from '../types'
import dayjs from 'dayjs'

export default function MeetingsList() {
  const [searchParams] = useSearchParams()
  const childId = searchParams.get('child_id')
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [children, setChildren] = useState<Child[]>([])
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    child_id: childId || '',
    title: '',
    date: '',
    participant_ids: [] as number[],
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadData()
  }, [childId])

  const loadData = async () => {
    try {
      const [meetingsRes, childrenRes, teamRes] = await Promise.all([
        childId ? meetingApi.getAll(parseInt(childId)) : meetingApi.getAll(),
        childApi.getAll(),
        teamMemberApi.getAll(),
      ])
      setMeetings(meetingsRes.data)
      setChildren(childrenRes.data)
      setTeamMembers(teamRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.child_id || !formData.title.trim()) return

    setSubmitting(true)
    try {
      await meetingApi.create({
        child_id: parseInt(formData.child_id),
        title: formData.title.trim(),
        date: formData.date || undefined,
        participant_ids: formData.participant_ids,
      })
      setFormData({ child_id: childId || '', title: '', date: '', participant_ids: [] })
      setShowModal(false)
      loadData()
    } catch (error) {
      console.error('Failed to create meeting:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const toggleParticipant = (memberId: number) => {
    setFormData((prev) => ({
      ...prev,
      participant_ids: prev.participant_ids.includes(memberId)
        ? prev.participant_ids.filter((id) => id !== memberId)
        : [...prev.participant_ids, memberId],
    }))
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      audio_uploaded: 'bg-blue-100 text-blue-800',
      processing: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待处理',
      audio_uploaded: '音频已上传',
      processing: '处理中',
      completed: '已完成',
      failed: '处理失败',
    }
    return texts[status] || status
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">会议管理</h1>
          <p className="text-gray-500 mt-1">管理IEP团队干预会议</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + 创建会议
        </button>
      </div>

      <div className="card">
        {meetings.length === 0 ? (
          <p className="text-gray-500 text-center py-12">暂无会议记录</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">会议主题</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">儿童</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">日期</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">状态</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">操作</th>
                </tr>
              </thead>
              <tbody>
                {meetings.map((meeting) => {
                  const child = children.find((c) => c.id === meeting.child_id)
                  return (
                    <tr key={meeting.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{meeting.title}</td>
                      <td className="py-3 px-4 text-gray-600">{child?.name || '-'}</td>
                      <td className="py-3 px-4 text-gray-600">
                        {dayjs(meeting.date).format('YYYY-MM-DD HH:mm')}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(meeting.status)}`}>
                          {getStatusText(meeting.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <Link to={`/meetings/${meeting.id}`} className="text-primary-600 hover:underline text-sm">
                          查看详情
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-6">创建会议</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">选择儿童 *</label>
                <select
                  className="input-field"
                  value={formData.child_id}
                  onChange={(e) => setFormData({ ...formData, child_id: e.target.value })}
                  required
                >
                  <option value="">请选择儿童</option>
                  {children.map((child) => (
                    <option key={child.id} value={child.id}>
                      {child.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">会议主题 *</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="例如：月度IEP进展评估会议"
                  required
                />
              </div>
              <div>
                <label className="label">会议日期</label>
                <input
                  type="datetime-local"
                  className="input-field"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                />
              </div>
              <div>
                <label className="label">参会人员</label>
                <div className="space-y-2 mt-2">
                  {teamMembers.map((member) => (
                    <label
                      key={member.id}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                    >
                      <input
                        type="checkbox"
                        checked={formData.participant_ids.includes(member.id)}
                        onChange={() => toggleParticipant(member.id)}
                        className="w-4 h-4 text-primary-600 rounded"
                      />
                      <div>
                        <div className="font-medium text-gray-900">{member.name}</div>
                        <div className="text-sm text-gray-500">{member.role}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">
                  取消
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={submitting}>
                  {submitting ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
