import { useEffect, useState } from 'react'
import { teamMemberApi } from '../services/api'
import type { TeamMember } from '../types'
import dayjs from 'dayjs'

export default function TeamMembers() {
  const [members, setMembers] = useState<TeamMember[]>([])
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({ name: '', role: '', email: '' })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadMembers()
  }, [])

  const loadMembers = async () => {
    try {
      const res = await teamMemberApi.getAll()
      setMembers(res.data)
    } catch (error) {
      console.error('Failed to load members:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim() || !formData.role.trim() || !formData.email.trim()) return

    setSubmitting(true)
    try {
      await teamMemberApi.create({
        name: formData.name.trim(),
        role: formData.role.trim(),
        email: formData.email.trim(),
      })
      setFormData({ name: '', role: '', email: '' })
      setShowModal(false)
      loadMembers()
    } catch (error) {
      console.error('Failed to create member:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const getRoleIcon = (role: string) => {
    if (role.includes('医生')) return '👨‍⚕️'
    if (role.includes('治疗师') || role.includes('语言')) return '🎤'
    if (role.includes('家长')) return '👨‍👩‍👧'
    if (role.includes('老师') || role.includes('教育')) return '👩‍🏫'
    if (role.includes('心理')) return '🧠'
    return '👤'
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">团队成员</h1>
          <p className="text-gray-500 mt-1">管理IEP干预团队成员</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + 添加成员
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {members.map((member) => (
          <div key={member.id} className="card">
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center text-2xl">
                {getRoleIcon(member.role)}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{member.name}</h3>
                <p className="text-primary-600 font-medium">{member.role}</p>
                <p className="text-sm text-gray-500 mt-1">{member.email}</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
              加入于 {dayjs(member.created_at).format('YYYY-MM-DD')}
            </div>
          </div>
        ))}
      </div>

      {members.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-500">暂无团队成员</p>
          <button onClick={() => setShowModal(true)} className="btn-primary mt-4">
            添加第一位成员
          </button>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold mb-6">添加团队成员</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">姓名 *</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="label">角色 *</label>
                <select
                  className="input-field"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                >
                  <option value="">请选择角色</option>
                  <option value="语言治疗师">语言治疗师</option>
                  <option value="家长">家长</option>
                  <option value="医生">医生</option>
                  <option value="特教老师">特教老师</option>
                  <option value="心理咨询师">心理咨询师</option>
                  <option value="作业治疗师">作业治疗师</option>
                  <option value="物理治疗师">物理治疗师</option>
                  <option value="其他">其他</option>
                </select>
              </div>
              <div>
                <label className="label">邮箱 *</label>
                <input
                  type="email"
                  className="input-field"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1">
                  取消
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={submitting}>
                  {submitting ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
