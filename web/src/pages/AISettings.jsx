import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Sparkles, CheckCircle2, Loader2, ExternalLink, Eye, EyeOff,
  Shield, Trash2, Edit3, Key, AlertTriangle, X
} from 'lucide-react'

export default function AISettings() {
  const navigate = useNavigate()
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [status, setStatus] = useState(null)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [editing, setEditing] = useState(false)
  const [hasUserKey, setHasUserKey] = useState(false)
  const [usingDefault, setUsingDefault] = useState(false)

  // Load current status on mount
  const refreshStatus = async () => {
    try {
      const r = await fetch('/api/ai/config-status')
      const d = await r.json()
      setStatus(d.available ? 'available' : 'not_configured')
      setHasUserKey(!!d.configured)
      setUsingDefault(!!d.using_default)
      if (d.configured) {
        setEditing(false)
        setApiKey('')
      }
    } catch (e) {
      setStatus('not_configured')
      setHasUserKey(false)
      setUsingDefault(false)
    }
  }

  useEffect(() => { refreshStatus() }, [])

  const handleSave = async () => {
    if (!apiKey.trim()) return
    setSaving(true)
    setSaveMsg(null)
    try {
      const r = await fetch('/api/ai/save-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey.trim() }),
      })
      const d = await r.json()
      setSaveMsg({ success: d.success, text: d.message })
      if (d.success) {
        setApiKey('')
        setEditing(false)
        await refreshStatus()
        setTestResult(null)
      }
    } catch (e) {
      setSaveMsg({ success: false, text: '保存失败，请重试。' })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const r = await fetch('/api/ai/test-connection', { method: 'POST' })
      const d = await r.json()
      setTestResult(d)
    } catch (e) {
      setTestResult({ success: false, message: '网络错误，请检查连接。' })
    } finally {
      setTesting(false)
    }
  }

  const handleDelete = async () => {
    setShowDeleteModal(false)
    try {
      await fetch('/api/ai/save-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: '' }),
      })
      setApiKey('')
      setTestResult(null)
      setEditing(false)
      await refreshStatus()
      setSaveMsg({ success: true, text: '你的 API Key 已删除。' })
    } catch (e) {
      setSaveMsg({ success: false, text: '删除失败，请重试。' })
    }
  }

  return (
    <div className="page animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/settings')} className="ios-icon-button" aria-label="Back">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            AI 服务设置
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
            管理你的 API Key 与 AI 服务状态
          </p>
        </div>
      </div>

      {/* ═══ API Status Card ═══ */}
      <div
        className="rounded-2xl p-5 mb-4"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <Key size={16} style={{ color: 'var(--accent)' }} />
            <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              DeepSeek API
            </span>
          </div>
          {/* Status dot */}
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{
                backgroundColor: status === 'available' ? 'var(--success)' : 'var(--text-tertiary)',
                boxShadow: status === 'available'
                  ? '0 0 6px var(--success)'
                  : 'none',
              }}
            />
            <span className="text-xs font-medium" style={{
              color: status === 'available' ? 'var(--success)' : 'var(--text-tertiary)',
            }}>
              {status === 'available' ? 'AI 服务可用' : 'AI 服务未配置'}
            </span>
          </div>
        </div>

        {/* Key display / input */}
        {hasUserKey && !editing ? (
          <>
            {/* Status badge — no key preview (stored securely in Windows Credential Manager) */}
            <div
              className="rounded-xl p-3 mb-3 flex items-center gap-2"
              style={{ backgroundColor: 'var(--surface-tertiary)' }}
            >
              <Shield size={13} style={{ color: 'var(--success)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--success)' }}>
                API Key 已安全存储在 Windows 凭据管理器
              </span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleTest}
                disabled={testing}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95 disabled:opacity-40"
                style={{
                  backgroundColor: 'var(--surface-tertiary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border)',
                }}
              >
                {testing ? <Loader2 size={14} className="animate-spin" /> : null}
                {testing ? '测试中...' : '测试连接'}
              </button>
              <button
                onClick={() => { setEditing(true); setSaveMsg(null); setTestResult(null) }}
                className="flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95"
                style={{
                  backgroundColor: 'var(--accent-subtle)',
                  color: 'var(--accent)',
                  border: 'none',
                }}
              >
                <Edit3 size={13} />
                修改
              </button>
              <button
                onClick={() => setShowDeleteModal(true)}
                className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:bg-[var(--danger-subtle)] active:scale-95"
                style={{
                  color: 'var(--danger)',
                  backgroundColor: 'transparent',
                  border: '1px solid var(--danger)',
                }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          </>
        ) : (
          <>
            {usingDefault && (
              <div
                className="mb-3 px-3 py-2 rounded-xl text-xs font-medium"
                style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}
              >
                当前通过环境变量提供了默认凭据，AI 功能已可用。配置你自己的 Key 后，将优先使用你的 Key。
              </div>
            )}
            <div className="relative mb-3">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={editing ? '输入新的 API Key' : 'sk-xxxxxxxxxxxxxxxxxxxxxxxx'}
                className="input pr-12 text-sm"
                style={{ fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.03em' }}
                spellCheck={false}
                autoComplete="off"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-all hover:bg-[var(--surface-tertiary)]"
                style={{ color: 'var(--text-tertiary)' }}
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving || !apiKey.trim()}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95 disabled:opacity-40"
                style={{ backgroundColor: 'var(--accent)', color: '#fff', border: 'none' }}
              >
                {saving ? '保存中...' : editing ? '更新 API Key' : '保存 API Key'}
              </button>
              {editing && (
                <button
                  onClick={() => { setEditing(false); setApiKey(''); setSaveMsg(null) }}
                  className="px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
                  style={{
                    backgroundColor: 'var(--surface-tertiary)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border)',
                  }}
                >
                  取消
                </button>
              )}
            </div>
          </>
        )}

        {/* Save / feedback message */}
        {saveMsg && (
          <div
            className="mt-3 px-3 py-2 rounded-xl flex items-center gap-2 animate-scale-in"
            style={{
              backgroundColor: saveMsg.success ? 'var(--success-subtle)' : 'var(--danger-subtle)',
            }}
          >
            {saveMsg.success
              ? <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
              : <AlertTriangle size={14} style={{ color: 'var(--danger)' }} />
            }
            <span className="text-xs font-medium" style={{
              color: saveMsg.success ? 'var(--success)' : 'var(--danger)',
            }}>
              {saveMsg.text}
            </span>
          </div>
        )}
      </div>

      {/* Test result card */}
      {testResult && (
        <div
          className="rounded-2xl p-4 mb-4 animate-scale-in"
          style={{
            backgroundColor: testResult.success ? 'var(--success-subtle)' : 'var(--danger-subtle)',
            border: `1px solid ${testResult.success ? 'var(--success)' : 'var(--danger)'}`,
          }}
        >
          <div className="flex items-center gap-2">
            {testResult.success
              ? <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />
              : <X size={16} style={{ color: 'var(--danger)' }} />
            }
            <span className="text-sm font-medium" style={{
              color: testResult.success ? 'var(--success)' : 'var(--danger)',
            }}>
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      {/* AI Features card */}
      <div
        className="rounded-2xl p-5 mb-4"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}
      >
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
          <Sparkles size={14} className="inline mr-1.5" style={{ color: 'var(--accent)' }} />
          AI 智能功能
        </h3>
        <div className="space-y-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <p>• 生成高质量英文例句（真实语境，非模板）</p>
          <p>• 提供自然流畅的中文翻译</p>
          <p>• AI 记忆提示，帮助联想记忆</p>
          <p>• 例句自动缓存，不重复消耗 Token</p>
        </div>
        {!hasUserKey && (
          <div
            className="mt-3 px-3 py-2 rounded-xl text-xs font-medium"
            style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}
          >
            配置你自己的 API Key 后，将优先使用你的 Key（未配置时 AI 功能不可用）
          </div>
        )}
      </div>

      {/* Privacy note */}
      <div
        className="rounded-2xl p-4 mb-4"
        style={{ backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-start gap-2">
          <Shield size={14} style={{ color: 'var(--text-tertiary)', marginTop: 1 }} />
          <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            <p className="font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>隐私说明</p>
            <p>• API Key 仅存储在本机，不会上传或共享</p>
            <p>• Token 消耗由您的 DeepSeek 账户承担</p>
            <p>• 例句缓存可减少重复 API 调用</p>
          </div>
        </div>
      </div>

      {/* DeepSeek link */}
      <a
        href="https://platform.deepseek.com/"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-1.5 py-2 text-xs transition-all hover:opacity-70"
        style={{ color: 'var(--text-tertiary)' }}
      >
        获取 API Key：DeepSeek API 平台
        <ExternalLink size={11} />
      </a>

      {/* ═══ Delete Confirmation Modal ═══ */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-6"
          style={{
            backgroundColor: 'rgba(0,0,0,0.55)',
            backdropFilter: 'blur(6px)',
            WebkitBackdropFilter: 'blur(6px)',
            animation: 'animOverlayIn 0.25s ease forwards',
          }}
          onClick={() => setShowDeleteModal(false)}
        >
          <div
            className="rounded-2xl p-6 max-w-sm w-full"
            style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border)',
              boxShadow: '0 24px 64px rgba(0,0,0,0.3)',
              animation: 'animPanelIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Icon */}
            <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{ backgroundColor: 'var(--danger-subtle)' }}>
              <AlertTriangle size={22} style={{ color: 'var(--danger)' }} />
            </div>

            <h3 className="text-base font-bold text-center mb-2" style={{ color: 'var(--text-primary)' }}>
              确认删除 API Key？
            </h3>
            <p className="text-sm text-center mb-6 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              删除后，AI 功能将不可用，直到你重新配置 API Key。是否继续？
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 hover:bg-[var(--surface-tertiary)] active:scale-95"
                style={{
                  backgroundColor: 'transparent',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border)',
                }}
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                className="flex-1 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95"
                style={{
                  backgroundColor: 'var(--danger)',
                  color: '#fff',
                  border: 'none',
                  boxShadow: '0 2px 12px rgba(255,59,48,0.35)',
                }}
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Version */}
      <div className="mt-6 text-center">
        <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>
          WordMaster v0.1.0 Beta
        </span>
      </div>
    </div>
  )
}
