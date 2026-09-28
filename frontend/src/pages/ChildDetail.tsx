import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { childApi, behaviorApi, meetingApi } from '../services/api'
import type { Child, BehaviorRecord, BehaviorChartData, Meeting } from '../types'
import dayjs from 'dayjs'

export default function ChildDetail() {
  const { id } = useParams<{ id: string }>()
  const [child, setChild] = useState<Child | null>(null)
  const [behaviorRecords, setBehaviorRecords] = useState<BehaviorRecord[]>([])
  const [chartData, setChartData] = useState<BehaviorChartData[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [showRecordModal, setShowRecordModal] = useState(false)
  const [recordForm, setRecordForm] = useState({
    behavior_type: '',
    frequency: '',
    intensity: '',
    duration: '',
    notes: '',
    target_behavior: false,
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (id) {
      loadData(parseInt(id))
    }
  }, [id])

  const loadData = async (childId: number) => {
    try {
      const [childRes, recordsRes, chartRes, meetingsRes] = await Promise.all([
        childApi.getById(childId),
        behaviorApi.getByChildId(childId),
        behaviorApi.getChartData(childId),
        meetingApi.getAll(childId),
      ])
      setChild(childRes.data)
      setBehaviorRecords(recordsRes.data)
      setChartData(chartRes.data)
      setMeetings(meetingsRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRecordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id || !recordForm.behavior_type.trim()) return

    setSubmitting(true)
    try {
      await behaviorApi.create({
        child_id: parseInt(id),
        behavior_type: recordForm.behavior_type.trim(),
        frequency: parseFloat(recordForm.frequency),
        intensity: recordForm.intensity ? parseInt(recordForm.intensity) : undefined,
        duration: recordForm.duration ? parseFloat(recordForm.duration) : undefined,
        notes: recordForm.notes.trim() || undefined,
        target_behavior: recordForm.target_behavior,
      })
      setRecordForm({
        behavior_type: '',
        frequency: '',
        intensity: '',
        duration: '',
        notes: '',
        target_behavior: false,
      })
      setShowRecordModal(false)
      loadData(parseInt(id))
    } catch (error) {
      console.error('Failed to create record:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const prepareChartData = () => {
    const grouped: Record<string, Record<string, number>> = {}
    chartData.forEach((item) => {
      if (!grouped[item.date]) {
        grouped[item.date] = {}
      }
      grouped[item.date][item.behavior_type] = item.frequency
    })

    const allBehaviors = [...new Set(chartData.map((d) => d.behavior_type))]
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

    return {
      data: Object.entries(grouped).map(([date, behaviors]) => ({
        date,
        ...behaviors,
      })),
      behaviors: allBehaviors.map((b, i) => ({ name: b, color: colors[i % colors.length] })),
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!child) {
    return <div className="text-center py-12">未找到儿童信息</div>
  }

  const { data: chartDataset, behaviors: behaviorTypes } = prepareChartData()

  return (
    <div>
      <div className="mb-8">
        <Link to="/children" className="text-primary-600 hover:underline text-sm mb-4 inline-block">
          ← 返回列表
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{child.name}</h1>
            <p className="text-gray-500 mt-1">
              {child.age && `${child.age} 岁`}
              {child.diagnosis && ` · ${child.diagnosis}`}
            </p>
          </div>
          <button onClick={() => setShowRecordModal(true)} className="btn-primary">
            + 添加行为记录
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">行为频率趋势图</h2>
          {chartDataset.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartDataset}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  {behaviorTypes.map((behavior) => (
                    <Line
                      key={behavior.name}
                      type="monotone"
                      dataKey={behavior.name}
                      stroke={behavior.color}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-12">暂无行为记录数据</p>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">行为类型统计</h2>
          {chartDataset.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartDataset}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  {behaviorTypes.map((behavior) => (
                    <Bar key={behavior.name} dataKey={behavior.name} fill={behavior.color} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-12">暂无行为记录数据</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">行为记录</h2>
            <span className="text-sm text-gray-500">共 {behaviorRecords.length} 条</span>
          </div>
          {behaviorRecords.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无行为记录</p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {behaviorRecords.slice(0, 10).map((record) => (
                <div key={record.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{record.behavior_type}</span>
                    {record.target_behavior && (
                      <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full">
                        目标行为
                      </span>
                    )}
                  </div>
                  <div className="flex gap-4 mt-2 text-sm text-gray-600">
                    <span>频率: {record.frequency}</span>
                    {record.intensity && <span>强度: {record.intensity}</span>}
                    {record.duration && <span>持续: {record.duration}分钟</span>}
                  </div>
                  {record.notes && <p className="text-sm text-gray-500 mt-2">{record.notes}</p>}
                  <p className="text-xs text-gray-400 mt-2">
                    {dayjs(record.recorded_at).format('YYYY-MM-DD HH:mm')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">相关会议</h2>
            <Link to={`/meetings?child_id=${child.id}`} className="text-primary-600 text-sm hover:underline">
              查看全部
            </Link>
          </div>
          {meetings.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无会议记录</p>
          ) : (
            <div className="space-y-3">
              {meetings.slice(0, 5).map((meeting) => (
                <Link key={meeting.id} to={`/meetings/${meeting.id}`} className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="font-medium text-gray-900">{meeting.title}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    {dayjs(meeting.date).format('YYYY-MM-DD')}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {showRecordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-6">添加行为记录</h2>
            <form onSubmit={handleRecordSubmit} className="space-y-4">
              <div>
                <label className="label">行为类型 *</label>
                <input
                  type="text"
                  className="input-field"
                  value={recordForm.behavior_type}
                  onChange={(e) => setRecordForm({ ...recordForm, behavior_type: e.target.value })}
                  placeholder="例如：目光接触、自我刺激、语言表达等"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">发生频率 *</label>
                  <input
                    type="number"
                    step="0.1"
                    className="input-field"
                    value={recordForm.frequency}
                    onChange={(e) => setRecordForm({ ...recordForm, frequency: e.target.value })}
                    placeholder="次/小时"
                    required
                  />
                </div>
                <div>
                  <label className="label">强度等级 (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    className="input-field"
                    value={recordForm.intensity}
                    onChange={(e) => setRecordForm({ ...recordForm, intensity: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="label">持续时间 (分钟)</label>
                <input
                  type="number"
                  step="0.1"
                  className="input-field"
                  value={recordForm.duration}
                  onChange={(e) => setRecordForm({ ...recordForm, duration: e.target.value })}
                />
              </div>
              <div>
                <label className="label">备注</label>
                <textarea
                  className="input-field"
                  value={recordForm.notes}
                  onChange={(e) => setRecordForm({ ...recordForm, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="target_behavior"
                  checked={recordForm.target_behavior}
                  onChange={(e) => setRecordForm({ ...recordForm, target_behavior: e.target.checked })}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <label htmlFor="target_behavior" className="text-sm text-gray-700">
                  标记为目标行为
                </label>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowRecordModal(false)} className="btn-secondary flex-1">
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
