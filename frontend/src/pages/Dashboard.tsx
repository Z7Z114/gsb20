import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { childApi, meetingApi, teamMemberApi } from '../services/api'
import type { Child, Meeting, TeamMember } from '../types'
import dayjs from 'dayjs'

export default function Dashboard() {
  const [children, setChildren] = useState<Child[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [childrenRes, meetingsRes, teamRes] = await Promise.all([
        childApi.getAll(),
        meetingApi.getAll(),
        teamMemberApi.getAll(),
      ])
      setChildren(childrenRes.data)
      setMeetings(meetingsRes.data)
      setTeamMembers(teamRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  const recentMeetings = meetings.slice(0, 5)

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

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
        <p className="text-gray-500 mt-1">自闭症儿童干预IEP会议管理系统</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">儿童总数</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{children.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-2xl">
              👶
            </div>
          </div>
          <Link to="/children" className="text-primary-600 text-sm hover:underline mt-4 inline-block">
            查看全部 →
          </Link>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">会议总数</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{meetings.length}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-2xl">
              📋
            </div>
          </div>
          <Link to="/meetings" className="text-primary-600 text-sm hover:underline mt-4 inline-block">
            查看全部 →
          </Link>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">团队成员</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{teamMembers.length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center text-2xl">
              👥
            </div>
          </div>
          <Link to="/team" className="text-primary-600 text-sm hover:underline mt-4 inline-block">
            查看全部 →
          </Link>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">最近会议</h2>
          <Link to="/meetings" className="text-primary-600 text-sm hover:underline">
            查看全部
          </Link>
        </div>

        {recentMeetings.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无会议记录</p>
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
                {recentMeetings.map((meeting) => {
                  const child = children.find((c) => c.id === meeting.child_id)
                  return (
                    <tr key={meeting.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{meeting.title}</td>
                      <td className="py-3 px-4 text-gray-600">{child?.name || '-'}</td>
                      <td className="py-3 px-4 text-gray-600">
                        {dayjs(meeting.date).format('YYYY-MM-DD')}
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
    </div>
  )
}
