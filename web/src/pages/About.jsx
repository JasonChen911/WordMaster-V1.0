import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, User, Coffee, Mail, X, Sparkles, Brain, Layers, Target, BookMarked, Repeat } from 'lucide-react'

const FEATURES = [
  { icon: BookMarked, title: 'AI 驱动词汇提取', desc: '从任意材料自动提取重点词汇，生成词书' },
  { icon: Repeat, title: 'FSRS 自适应学习', desc: '根据每次作答自适应安排复习时间' },
  { icon: Brain, title: 'AI 学习诊断', desc: '基于真实数据诊断错因、给出建议' },
  { icon: Target, title: '智能错因分析', desc: '易混词辨析、针对性练习生成' },
  { icon: Layers, title: '课程材料词表生成', desc: '教师上传材料，一键生成课程词书' },
]

export default function About() {
  const navigate = useNavigate()
  const [showSponsor, setShowSponsor] = useState(false)

  return (
    <div className="page animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/settings')} className="ios-icon-button" aria-label="Back">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          关于 WordMaster AI
        </h1>
      </div>

      {/* Positioning */}
      <div className="rounded-2xl p-6 mb-4 text-center"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ backgroundColor: 'var(--accent-subtle)' }}>
          <Sparkles size={24} style={{ color: 'var(--accent)' }} />
        </div>
        <h2 className="text-lg font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          WordMaster AI
        </h2>
        <p className="text-sm mb-3" style={{ color: 'var(--accent)' }}>
          让 AI 决定学什么，让 FSRS 决定什么时候复习。
        </p>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
          面向高校英语课程、四六级与考研场景的 AI 驱动、本地优先、自适应词汇学习与教学平台。
        </p>
      </div>

      {/* Feature list */}
      <div className="rounded-2xl p-5 mb-4" style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
        <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>核心能力</h3>
        <div className="space-y-3">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                <Icon size={15} style={{ color: 'var(--accent)' }} />
              </div>
              <div>
                <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</div>
                <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Creator card */}
      <div className="rounded-2xl p-6 mb-4 text-center"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
        <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3"
          style={{ backgroundColor: 'var(--accent-subtle)' }}>
          <User size={24} style={{ color: 'var(--accent)' }} />
        </div>
        <div className="space-y-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <div className="flex items-center justify-center gap-2">
            <span style={{ color: 'var(--text-tertiary)' }}>制作人：</span>
            <span className="font-medium" style={{ color: 'var(--text-primary)' }}>JasonChen</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <Mail size={13} style={{ color: 'var(--text-tertiary)' }} />
            <span style={{ color: 'var(--accent)' }}>cby080812b@outlook.com</span>
          </div>
        </div>
      </div>

      {/* Sponsor button */}
      <button
        onClick={() => setShowSponsor(true)}
        className="w-full py-3 rounded-2xl text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.98] flex items-center justify-center gap-2"
        style={{
          backgroundColor: 'var(--warning-subtle)',
          color: 'var(--warning)',
          border: '1px solid rgba(255,149,0,0.2)',
        }}>
        <Coffee size={16} />
        赞助我
      </button>

      {/* Sponsor modal */}
      {showSponsor && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-6"
          style={{ backgroundColor: 'rgba(0,0,0,0.60)', backdropFilter: 'blur(10px)' }}
          onClick={() => setShowSponsor(false)}
        >
          <div
            className="rounded-3xl p-6 max-w-sm w-full text-center animate-scale-in"
            style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-end mb-2">
              <button onClick={() => setShowSponsor(false)}
                className="p-1.5 rounded-full transition-all hover:bg-[var(--surface-tertiary)]"
                style={{ color: 'var(--text-tertiary)' }}>
                <X size={16} />
              </button>
            </div>

            <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
              支持 WordMaster
            </h3>

            <div className="w-48 h-48 mx-auto mb-4 rounded-2xl flex items-center justify-center overflow-hidden"
              style={{ backgroundColor: '#fff', border: '1px solid var(--border)' }}>
              <img
                src="/sponsor-qr.jpg"
                alt="收款码"
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none'
                  const span = document.createElement('span')
                  span.style.cssText = 'color: var(--text-tertiary); font-size: 0.75rem;'
                  span.textContent = '收款码图片未找到'
                  e.target.parentElement.appendChild(span)
                }}
              />
            </div>

            <div className="space-y-1.5 mb-1">
              <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>软件制作不易</p>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                如果你觉得 WordMaster 还不错，
              </p>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                可以请哥布林喝杯咖啡！
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
