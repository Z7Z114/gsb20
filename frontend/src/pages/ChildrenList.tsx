import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { childApi } from '../services/api'
import type { Child } from '../types'
import dayjs from 'dayjs'

export default function ChildrenList() {
  const [children, setChildren] = useState<Child[]>([])
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({ name: '', age: '', diagnosis: '' })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadChildren()
  }, [])

  const loadChildren = async () => {
    try {
      const res = await childApi.getAll()
      setChildren(res.data)
    } catch (error) {
      console.error('Failed to load children:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    setSubmitting(true)
    try {
      await childApi.create({
        name: formData.name.trim(),
        age: formData.age ? parseInt(formData.age) : undefined,
        diagnosis: formData.diagnosis.trim() || undefined,
      })
      setFormData({ name: '', age: '', diagnosis: '' })
      setShowModal(false)
      loadChildren()
    } catch (error) {
      console.error('Failed to create child:', error)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">儿童管理</h1>
          <p className="text-gray-500 mt-1">管理自闭症儿童基本信息</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary">
          + 添加儿童
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {children.map((child) => (
          <Link key={child.id} to={`/children/${child.id}`} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{child.name}</h3>
                {child.age && (
                  <p className="text-gray-500 mt-1">{child.age} 岁</p>
                )}
                {child.diagnosis && (
                  <p className="text-sm text-gray-600 mt-2">{child.diagnosis}</p>
                )}
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-xl">
                👶
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
              创建于 {dayjs(child.created_at).format('YYYY-MM-DD')}
            </div>
          </Link>
        ))}
      </div>

      {children.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-500">暂无儿童记录</p>
          <button onClick={() => setShowModal(true)} className="btn-primary mt-4">
            添加第一个儿童
          </button>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold mb-6">添加儿童</h2>
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
                <label className="label">年龄</label>
                <input
                  type="number"
                  className="input-field"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  min="0"
                  max="18"
                />
              </div>
              <div>
                <label className="label">诊断信息</label>
                <textarea
                  className="input-field"
                  value={formData.diagnosis}
                  onChange={(e) => setFormData({ ...formData, diagnosis: e.target.value })}
                  rows={3}
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
