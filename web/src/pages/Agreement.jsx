import { useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText } from 'lucide-react'

export default function Agreement() {
  const navigate = useNavigate()

  return (
    <div className="page animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/settings')} className="ios-icon-button" aria-label="Back">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          软件使用协议
        </h1>
      </div>

      <div className="rounded-2xl p-6"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2.5 mb-4">
          <FileText size={18} style={{ color: 'var(--accent)' }} />
          <h2 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
            WordMaster 软件使用协议
          </h2>
        </div>

        <div className="text-sm leading-7 space-y-5" style={{ color: 'var(--text-secondary)' }}>
          <p>欢迎使用 WordMaster。</p>
          <p>本软件是一款用于英语词汇学习的个人学习工具。</p>

          <div>
            <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>一、软件功能</h3>
            <p>WordMaster 提供：</p>
            <ol className="list-decimal pl-5 space-y-1 mt-1">
              <li>单词学习功能</li>
              <li>词书管理功能</li>
              <li>学习进度记录功能</li>
              <li>单词复习辅助功能</li>
            </ol>
            <p className="mt-2">本软件旨在帮助用户提高英语学习效率。</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>二、用户使用</h3>
            <p>用户可以根据自身学习需求使用本软件。</p>
            <p>软件提供的学习内容仅作为学习辅助工具，不保证学习结果。</p>
            <p className="mt-1">用户应合理安排学习时间，根据自身情况制定学习计划。</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>三、数据说明</h3>
            <p>WordMaster 可能在本地保存：</p>
            <ul className="list-disc pl-5 space-y-1 mt-1">
              <li>学习记录</li>
              <li>词书信息</li>
              <li>学习进度</li>
            </ul>
            <p className="mt-2">这些数据用于提供更好的学习体验。</p>
            <p>目前版本不会主动收集用户个人信息。</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>四、免责声明</h3>
            <p>本软件仅用于个人学习用途。</p>
            <p>软件开发者不对因使用本软件产生的学习效果差异承担责任。</p>
            <p className="mt-1">用户应遵守相关法律法规，不得利用本软件进行违法活动。</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>五、版本更新</h3>
            <p>WordMaster 会持续优化功能。</p>
            <p>未来可能增加新的学习功能。</p>
          </div>

          <p className="pt-2" style={{ color: 'var(--text-tertiary)' }}>
            感谢使用 WordMaster。
          </p>
        </div>
      </div>
    </div>
  )
}
