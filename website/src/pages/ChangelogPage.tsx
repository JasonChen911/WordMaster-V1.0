import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowUpRight, Check, Clock3 } from 'lucide-react'
import Reveal from '../components/Reveal'
import release from '../release.generated.json'

const groups = [
  { title: '学习与记忆', items: ['接入 FSRS 间隔重复，按四级反馈调整单词复习安排。', '在学习页解释为什么今天需要复习这个词。', '加入拼写、填空、游戏化练习和错词管理。'] },
  { title: 'AI 辅助', items: ['三位 AI 导师支持独立对话与本机历史记录。', 'AI 阅读可保存生成的文章、题目与题型，并可逐条删除。', '从本地材料提取重点词汇，确认后生成词书。'] },
  { title: '桌面体验', items: ['优化启动检测与前端资源校验。', '加入可选背景、深色模式和发音设置。', '提供 Windows 安装程序及 Ubuntu 24.04 x64 测试包。'] },
]

export default function ChangelogPage() {
  return <section className="changelog-page container"><Reveal><span className="eyebrow">Release notes</span><h1>每一步改进，<br /><em>都有迹可循。</em></h1><p>以下记录当前 Beta 构建中已经实现的功能，不包含尚未上线的计划。</p></Reveal><div className="timeline"><div className="timeline-rail" /><Reveal className="release-entry"><div className="release-marker" /><div className="release-meta"><span className="release-badge"><span /> 当前构建</span><h2>v{release.version} Beta</h2><p><Clock3 size={15} /> 本地版本配置读取</p></div><div className="release-groups">{groups.map(group => <div key={group.title}><h3>{group.title}</h3><ul>{group.items.map(item => <li key={item}><Check size={16} /><span>{item}</span></li>)}</ul></div>)}</div></Reveal></div><Reveal className="changelog-actions"><Link to="/download/" className="button button-primary">获取当前版本 <ArrowUpRight size={16} /></Link><Link to="/" className="text-link"><ArrowLeft size={15} /> 返回首页</Link></Reveal></section>
}

