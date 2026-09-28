import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { meetingApi, childApi } from '../services/api'
import type { Meeting, Child, TranscriptSegment, MeetingParticipant, IEPSummaryResponse } from '../types'
import dayjs from 'dayjs'

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>()
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [child, setChild] = useState<Child | null>(null)
  const [participants, setParticipants] = useState<MeetingParticipant[]>([])
  const [transcripts, setTranscripts] = useState<TranscriptSegment[]>([])
  const [iepSummary, setIepSummary] = useState<IEPSummaryResponse | null>(null)
  const [status, setStatus] = useState<any>(null)
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [sendingEmail, setSendingEmail] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'iep' | 'email'>('overview')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      loadData(parseInt(id))
      const interval = setInterval(() => {
        checkStatus(parseInt(id))
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [id])

  const loadData = async (meetingId: number) => {
    try {
      const [meetingRes, participantsRes, transcriptsRes, iepRes] = await Promise.all([
        meetingApi.getById(meetingId),
        meetingApi.getParticipants(meetingId),
        meetingApi.getTranscripts(meetingId),
        meetingApi.getIepSummary(meetingId).catch(() => ({ data: null })),
      ])
      setMeeting(meetingRes.data)
      setParticipants(participantsRes.data)
      setTranscripts(transcriptsRes.data)
      if (iepRes.data) {
        setIepSummary(iepRes.data)
      }
      if (meetingRes.data.child_id) {
        const childRes = await childApi.getById(meetingRes.data.child_id)
        setChild(childRes.data)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkStatus = async (meetingId: number) => {
    try {
      const res = await meetingApi.getStatus(meetingId)
      setStatus(res.data)
      if (res.data.status === 'completed' && (!iepSummary || !transcripts.length)) {
        loadData(meetingId)
      }
    } catch (error) {
      console.error('Failed to check status:', error)
    }
  }

  const handleUpload = async () => {
    if (!id || !audioFile) return

    setUploading(true)
    try {
      await meetingApi.uploadAudio(parseInt(id), audioFile)
      setAudioFile(null)
      checkStatus(parseInt(id))
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Failed to upload audio:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!id) return

    setProcessing(true)
    try {
      await meetingApi.process(parseInt(id))
    } catch (error) {
      console.error('Failed to process meeting:', error)
    } finally {
      setProcessing(false)
    }
  }

  const handleSendEmail = async () => {
    if (!id) return

    setSendingEmail(true)
    try {
      await meetingApi.sendEmail(parseInt(id))
      alert('邮件发送成功！')
    } catch (error) {
      console.error('Failed to send email:', error)
      alert('邮件发送失败，请检查后端日志')
    } finally {
      setSendingEmail(false)
    }
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

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!meeting) {
    return <div className="text-center py-12">未找到会议信息</div>
  }

  return (
    <div>
      <div className="mb-8">
        <Link to="/meetings" className="text-primary-600 hover:underline text-sm mb-4 inline-block">
          ← 返回会议列表
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{meeting.title}</h1>
            <p className="text-gray-500 mt-1">
              {child?.name} · {dayjs(meeting.date).format('YYYY-MM-DD HH:mm')}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(meeting.status)}`}>
            {getStatusText(meeting.status)}
          </span>
        </div>
      </div>

      {meeting.status === 'pending' && (
        <div className="card mb-6 bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-3">第一步：上传会议音频</h3>
          <div className="flex gap-4 items-center">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-100 file:text-primary-700 hover:file:bg-primary-200"
            />
            <button
              onClick={handleUpload}
              disabled={!audioFile || uploading}
              className="btn-primary whitespace-nowrap"
            >
              {uploading ? '上传中...' : '上传'}
            </button>
          </div>
        </div>
      )}

      {meeting.status === 'audio_uploaded' && (
        <div className="card mb-6 bg-green-50 border-green-200">
          <h3 className="font-semibold text-green-900 mb-3">第二步：开始处理会议</h3>
          <p className="text-green-700 text-sm mb-4">
            音频已上传，点击下方按钮开始转写、角色区分和IEP摘要生成
          </p>
          <button onClick={handleProcess} disabled={processing} className="btn-primary">
            {processing ? '处理中...' : '开始处理'}
          </button>
        </div>
      )}

      {meeting.status === 'processing' && (
        <div className="card mb-6 bg-purple-50 border-purple-200">
          <h3 className="font-semibold text-purple-900 mb-3">会议处理中...</h3>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-purple-700">正在进行语音转写、角色区分和摘要生成，请稍候...</p>
          </div>
        </div>
      )}

      {meeting.status === 'completed' && (
        <div className="card mb-6 bg-green-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-green-900 mb-1">✓ 会议处理完成</h3>
              <p className="text-green-700 text-sm">转写、角色区分和IEP摘要已生成</p>
            </div>
            <button onClick={handleSendEmail} disabled={sendingEmail} className="btn-primary">
              {sendingEmail ? '发送中...' : '发送加密邮件'}
            </button>
          </div>
        </div>
      )}

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-8">
          {[
            { key: 'overview', label: '概览' },
            { key: 'transcript', label: '会议转写' },
            { key: 'iep', label: 'IEP摘要' },
            { key: 'email', label: '邮件发送' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.key
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">参会人员</h2>
            <div className="space-y-3">
              {participants.map((p) => (
                <div key={p.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center font-medium text-primary-700">
                    {p.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{p.name}</div>
                    <div className="text-sm text-gray-500">{p.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">处理状态</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-medium ${status?.has_audio ? 'bg-green-500' : 'bg-gray-300'}`}>
                  {status?.has_audio ? '✓' : '1'}
                </div>
                <span className={status?.has_audio ? 'text-gray-900' : 'text-gray-500'}>音频上传</span>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-medium ${status?.has_transcript ? 'bg-green-500' : 'bg-gray-300'}`}>
                  {status?.has_transcript ? '✓' : '2'}
                </div>
                <span className={status?.has_transcript ? 'text-gray-900' : 'text-gray-500'}>语音转写与角色区分</span>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-medium ${status?.has_summary ? 'bg-green-500' : 'bg-gray-300'}`}>
                  {status?.has_summary ? '✓' : '3'}
                </div>
                <span className={status?.has_summary ? 'text-gray-900' : 'text-gray-500'}>IEP摘要生成</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'transcript' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">会议转写记录</h2>
          {transcripts.length === 0 ? (
            <p className="text-gray-500 text-center py-12">暂无转写记录</p>
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {transcripts.map((seg) => (
                <div key={seg.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-medium text-primary-600">{seg.speaker}</span>
                    {seg.speaker_role && (
                      <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded-full">
                        {seg.speaker_role}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">
                      {formatTime(seg.start_time)} - {formatTime(seg.end_time)}
                    </span>
                  </div>
                  <p className="text-gray-700">{seg.text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'iep' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">IEP摘要与建议</h2>
          {!iepSummary || !iepSummary.summary ? (
            <p className="text-gray-500 text-center py-12">暂无IEP摘要</p>
          ) : (
            <div>
              {iepSummary.target_behaviors.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">🎯 目标行为</h3>
                  <div className="flex flex-wrap gap-2">
                    {iepSummary.target_behaviors.map((behavior, i) => (
                      <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                        {behavior}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {iepSummary.intervention_strategies.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">📋 干预策略</h3>
                  <div className="flex flex-wrap gap-2">
                    {iepSummary.intervention_strategies.map((strategy, i) => (
                      <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                        {strategy}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {iepSummary.progress_notes && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">📊 进展评估</h3>
                  <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">{iepSummary.progress_notes}</p>
                </div>
              )}

              {iepSummary.suggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">💡 调整建议</h3>
                  <ul className="space-y-2">
                    {iepSummary.suggestions.map((suggestion, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-primary-600 mt-1">•</span>
                        <span className="text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="font-medium text-gray-900 mb-3">📝 完整报告</h3>
                <div className="prose prose-sm max-w-none bg-gray-50 p-6 rounded-lg">
                  <ReactMarkdown>{iepSummary.summary}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'email' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">发送加密邮件</h2>
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">收件人</h3>
            <div className="space-y-2">
              {participants.map((p) => (
                <div key={p.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center font-medium text-primary-700 text-sm">
                    {p.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{p.name}</div>
                    <div className="text-sm text-gray-500">{p.email}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-yellow-900 mb-2">🔒 加密说明</h4>
            <p className="text-sm text-yellow-700">
              邮件内容将使用AES-256加密，收件人需要使用解密密钥才能查看完整的IEP报告。
              解密密钥将在邮件中提供。
            </p>
          </div>

          <button
            onClick={handleSendEmail}
            disabled={sendingEmail || meeting.status !== 'completed'}
            className="btn-primary w-full"
          >
            {sendingEmail ? '发送中...' : '发送加密邮件给所有参会人员'}
          </button>

          {meeting.status !== 'completed' && (
            <p className="text-sm text-gray-500 text-center mt-3">
              请等待会议处理完成后再发送邮件
            </p>
          )}
        </div>
      )}
    </div>
  )
}
