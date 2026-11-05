import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence, useReducedMotion, useScroll, useSpring, useTransform } from 'motion/react'
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Brain, Check, Download, Eye, FileText, Layers3, MessageCircle, Target } from 'lucide-react'
import Reveal from '../components/Reveal'

const demoAnswers = [
  { prompt: '如何理解 abandon？', answer: 'abandon 常表示“放弃”或“离弃”。记忆时先抓住核心动作：主动停止坚持或留下某事。再结合例句辨别语境。' },
  { prompt: '怎样安排单词复习？', answer: '先完成今天的到期词，再处理新词。遇到记不稳的词，选择“困难”或“忘记”，让后续复习间隔更贴近你的实际记忆状态。' },
  { prompt: '雅思写作如何积累表达？', answer: '按主题整理常用表达，记录完整例句。练习时先保证用词准确，再尝试同义改写；不要为使用复杂词而牺牲清晰度。' },
]

function SectionHeading({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return <div className="section-heading"><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{text}</p></div>
}

function Hero() {
  const reduceMotion = useReducedMotion()
  const stageRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: stageRef, offset: ['start end', 'center center'] })
  const spread = useSpring(scrollYProgress, { stiffness: 65, damping: 24 })
  const leftX = useTransform(spread, [0, 1], [105, -10])
  const rightX = useTransform(spread, [0, 1], [-105, 10])
  const leftRotate = useTransform(spread, [0, 1], [-2, -11])
  const rightRotate = useTransform(spread, [0, 1], [2, 11])
  const sideOpacity = useTransform(spread, [0, 0.5, 1], [0.15, 0.8, 1])
  return <section className="hero" aria-labelledby="hero-title">
    <div className="hero-wash" aria-hidden="true" />
    <div className="container hero-content">
      <motion.div className="hero-kicker" initial={reduceMotion ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
        英语学习，回到真正有效的节奏
      </motion.div>
      <motion.h1 id="hero-title" initial={reduceMotion ? false : { opacity: 0, y: 25 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.72, delay: 0.08 }}>WordMaster</motion.h1>
      <motion.p className="hero-title-cn" initial={reduceMotion ? false : { opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.72, delay: 0.17 }}>让每一次记忆，都更有价值。</motion.p>
      <motion.p className="hero-tagline" initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, delay: 0.26 }}>Learn Smarter. Remember Longer.</motion.p>
      <motion.p className="hero-description" initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, delay: 0.34 }}>融合人工智能与科学记忆算法，重新定义英语词汇学习体验。</motion.p>
      <motion.div className="hero-actions" initial={reduceMotion ? false : { opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, delay: 0.42 }}>
        <Link to="/download/" className="button button-primary"><Download size={17} /> 查看获取方式 <ArrowUpRight size={16} /></Link>
        <Link to="/#features" className="button button-secondary">探索功能 <ArrowDown size={16} /></Link>
      </motion.div>
      <motion.div className="hero-proof" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>Windows 桌面应用 <span /> v0.1.0 Beta <span /> 截图来自实际运行界面</motion.div>
      <motion.div ref={stageRef} className="hero-stage" initial={reduceMotion ? false : { opacity: 0, y: 55 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.85, delay: 0.38, ease: [0.22, 0.61, 0.36, 1] }}>
        <div className="app-window hero-main-window">
          <div className="window-bar"><div className="window-dots"><i /><i /><i /></div><span>WordMaster · 学习首页</span><span className="window-chip">真实界面</span></div>
          <img src="/images/wordmaster-home-real.png" alt="WordMaster 实际运行的学习首页，显示今日任务、词汇统计和学习入口" width="1075" height="865" fetchPriority="high" />
        </div>
        <motion.div className="hero-float hero-float-study" style={reduceMotion ? undefined : { x: leftX, rotate: leftRotate, opacity: sideOpacity }}><img src="/images/wordmaster-study-real.png" alt="WordMaster 实际运行的单词学习卡片" width="1075" height="865" /><span>01 / 专注学习</span></motion.div>
        <motion.div className="hero-float hero-float-tutor" style={reduceMotion ? undefined : { x: rightX, rotate: rightRotate, opacity: sideOpacity }}><img src="/images/wordmaster-tutor-real.png" alt="WordMaster 实际运行的 AI 导师页面" width="1075" height="865" /><span>02 / AI 辅助</span></motion.div>
      </motion.div>
    </div>
  </section>
}

function Features() {
  const [selectedGrade, setSelectedGrade] = useState<string | null>(null)
  return <section id="features" className="section features-section container">
    <Reveal><SectionHeading eyebrow="Made for everyday learning" title="专注学习，也理解你如何记忆。" text="从理解单词到安排复习，每一个模块都围绕真实学习动作设计。" /></Reveal>
    <div className="bento">
      <Reveal className="feature-card feature-tutor"><div className="feature-top"><span className="feature-number">01 / INTELLIGENCE</span><MessageCircle size={19} /></div><div className="feature-body"><h3>AI Tutor</h3><p>向三位不同方向的导师提问。解释用法、规划学习，或练习雅思表达。</p></div><div className="mini-conversation"><div className="mini-person"><img src="/images/emma.webp" alt="" loading="lazy" /></div><div><small>Emma · 英语老师</small><p>“abandon” 在这个句子里为什么是“放弃”？</p><div className="mini-answer">先看动作的对象，再判断是放弃计划、习惯，还是离开某处。</div></div></div><span className="demo-label">功能场景示意 · 非实时 AI</span></Reveal>
      <Reveal className="feature-card feature-memory" delay={0.05}><div className="feature-top"><span className="feature-number">02 / MEMORY</span><Brain size={19} /></div><div className="feature-body"><h3>FSRS 智能记忆</h3><p>根据学习反馈调整复习计划，让不稳的词更及时地回到你面前。</p></div><div className="memory-mini"><div className="memory-mini-line" /><span>学习</span><span>回忆</span><span>巩固</span></div></Reveal>
      <Reveal className="feature-card feature-practice"><div className="feature-top"><span className="feature-number">03 / PRACTICE</span><Target size={19} /></div><div className="feature-body"><h3>多样化练习</h3><p>拼写、填空和交互式练习，让认识一个词变成真正会用。</p></div><div className="practice-demo" aria-label="复习反馈交互示意"><span>你对这个词的掌握程度？</span><div>{['忘记', '困难', '一般', '简单'].map(grade => <button key={grade} className={selectedGrade === grade ? 'selected' : ''} onClick={() => setSelectedGrade(grade)} aria-pressed={selectedGrade === grade}>{grade}</button>)}</div><small>{selectedGrade ? `已选择“${selectedGrade}” · 界面示意，不会记录进度` : '试着选择一个反馈'}</small></div></Reveal>
      <Reveal className="feature-card feature-books" delay={0.04}><div className="feature-top"><span className="feature-number">04 / YOUR LIBRARY</span><Layers3 size={19} /></div><div className="feature-body"><h3>个性化词库</h3><p>使用内置词书，也能从本地材料提取重点词汇，建立自己的学习路径。</p></div><div className="book-stack"><span>IELTS · 高频词</span><span>CET-6 · 核心词</span><span>我的材料 · 自定义</span></div></Reveal>
      <Reveal className="feature-card feature-mistakes" delay={0.06}><div className="feature-top"><span className="feature-number">05 / REFLECTION</span><BookOpen size={19} /></div><div className="feature-body"><h3>错词管理</h3><p>记录薄弱词汇，回看错误类型，把下一次练习用在需要的地方。</p></div><div className="mistake-visual"><span>薄弱词</span><span>再次练习 <ArrowUpRight size={14} /></span></div></Reveal>
      <Reveal className="feature-card feature-focus" delay={0.08}><div className="feature-focus-copy"><div className="feature-top"><span className="feature-number">06 / FOCUS</span><Eye size={19} /></div><div className="feature-body"><h3>清晰的学习体验</h3><p>少一点干扰，多一点专注。每一次打开，都知道下一步该学什么。</p></div></div><div className="feature-focus-visual"><img src="/images/wordmaster-study-real.png" alt="真实的 WordMaster 学习卡片界面" width="1075" height="865" loading="lazy" /></div></Reveal>
    </div>
  </section>
}

function Intelligence() {
  const [selected, setSelected] = useState(0)
  const [showReply, setShowReply] = useState(true)
  const reduceMotion = useReducedMotion()
  const select = (index: number) => { setShowReply(false); setSelected(index); requestAnimationFrame(() => setShowReply(true)) }
  return <section id="intelligence" className="section intelligence-section"><div className="container intelligence-grid">
    <Reveal className="intelligence-copy"><span className="eyebrow">AI with purpose</span><h2>不是替你学习。<br /><em>是陪你理解。</em></h2><p>WordMaster 的 AI 导师用于解释单词、分析用法与提供学习建议。需要 API Key；基础学习功能可以独立使用。</p><div className="ai-bullets"><span><Check size={16} /> 单词用法与例句</span><span><Check size={16} /> 学习计划建议</span><span><Check size={16} /> 雅思表达练习</span></div><Link className="text-link" to="/download/">了解安装与配置 <ArrowUpRight size={16} /></Link></Reveal>
    <Reveal className="ai-demo" delay={0.08}><div className="demo-window-top"><div className="demo-window-title"><span className="demo-status" /> AI Tutor 交互示意</div><span>非实时 API</span></div><div className="demo-chat"><div className="demo-message user">{demoAnswers[selected].prompt}</div><AnimatePresence mode="wait">{showReply && <motion.div key={selected} className="demo-message assistant" initial={reduceMotion ? false : { opacity: 0, y: 10, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.32 }}><img src="/images/wordmaster-logo.webp" alt="" width="28" height="28" /><p>{demoAnswers[selected].answer}</p></motion.div>}</AnimatePresence></div><div className="demo-prompts">{demoAnswers.map((item, index) => <button key={item.prompt} onClick={() => select(index)} aria-pressed={selected === index}>{item.prompt}</button>)}</div><div className="demo-input">向 AI 导师提问… <ArrowUpRight size={16} /></div></Reveal>
  </div></section>
}

function MemoryEngine() {
  const [interval, setIntervalDays] = useState(6)
  const reduceMotion = useReducedMotion()
  const path = useMemo(() => {
    const points: string[] = []
    for (let day = 0; day <= 30; day += 0.15) {
      const sinceReview = day % interval
      const retention = 0.25 + 0.69 * Math.exp(-sinceReview / (interval * 0.75))
      const x = 25 + day / 30 * 650
      const y = 210 - retention * 150
      points.push(`${points.length ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`)
    }
    return points.join(' ')
  }, [interval])
  return <section id="memory" className="section memory-section container"><Reveal><SectionHeading eyebrow="The memory engine" title="把复习，安排在恰当的时候。" text="FSRS 根据你的四级反馈更新记忆状态，决定下一次复习时间。下面的曲线只解释原理，不代表真实用户数据。" /></Reveal><div className="memory-layout"><Reveal className="chart-panel"><div className="chart-header"><span>记忆保持趋势</span><span className="chart-disclaimer">算法原理示意 · 非真实数据</span></div><svg viewBox="0 0 700 240" role="img" aria-label={`记忆保持趋势示意，当前复习间隔为 ${interval} 天`}><g className="chart-grid"><line x1="25" y1="40" x2="675" y2="40" /><line x1="25" y1="110" x2="675" y2="110" /><line x1="25" y1="180" x2="675" y2="180" /><line x1="25" y1="210" x2="675" y2="210" /></g><motion.path key={interval} d={path} fill="none" stroke="var(--blue)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" initial={reduceMotion ? false : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.75, ease: 'easeOut' }} />{Array.from({ length: Math.floor(30 / interval) }, (_, index) => { const x = 25 + ((index + 1) * interval) / 30 * 650; return <g key={index}><line className="review-marker" x1={x} y1="45" x2={x} y2="210" /><circle cx={x} cy="209" r="5" fill="var(--blue)" /></g> })}<text x="25" y="235">学习开始</text><text x="610" y="235">时间推移</text></svg><div className="chart-legend"><span><i /> 概念性保持趋势</span><span><i /> 复习时点</span></div></Reveal><Reveal className="memory-controls" delay={0.06}><div className="control-icon"><Brain size={26} /></div><h3>试着调整复习间隔</h3><p>间隔越长，下一次复习前可能忘记的内容越多。实际软件会依据每个单词的学习反馈动态计算。</p><label htmlFor="interval-slider">示意间隔 <strong>{interval} 天</strong></label><input id="interval-slider" type="range" min="3" max="10" value={interval} onChange={event => setIntervalDays(Number(event.target.value))} /><div className="range-ends"><span>更频繁</span><span>更宽松</span></div><div className="grade-row"><span>忘记</span><span>困难</span><span>一般</span><span>简单</span></div><small>四级反馈对应软件实际学习流程</small></Reveal></div></section>
}

function Closing() {
  return <><section id="source" className="section source-section"><div className="container source-grid"><Reveal><span className="eyebrow">Project status · Beta</span><h2>认真对待每一行代码，<br />也认真对待发布承诺。</h2><p>WordMaster 源码已在 GitHub 公开，当前仍采用专有使用协议，尚未授予开源许可证。源码仓库不包含安装包；Linux 测试包在 GitHub Releases，Windows 安装包由官网提供。</p><a className="text-link" href="https://github.com/JasonChen911/WordMaster-V1.0" target="_blank" rel="noopener noreferrer">查看 GitHub 源码 <ArrowUpRight size={16} /></a></Reveal><Reveal className="stack-panel" delay={0.05}><div className="stack-head"><FileText size={18} /> 当前技术栈 <span>已实现</span></div><div><span>Frontend</span><strong>React · Vite · Tailwind</strong></div><div><span>Desktop</span><strong>PyWebView · Windows / Linux</strong></div><div><span>Backend</span><strong>FastAPI · SQLite</strong></div><div><span>Memory</span><strong>FSRS</strong></div></Reveal></div></section><section id="about" className="about-section container"><Reveal><span className="eyebrow">From the maker</span><h2>学习应该像对话，<br />而不是和遗忘赛跑。</h2><p>WordMaster 由 JasonChen 开发。它从一个简单的问题开始：有没有办法，让每天的词汇练习更清楚、更有反馈，也更容易坚持？</p><span className="about-signature">JasonChen <i /> WordMaster 开发者</span></Reveal></section><section className="closing-cta"><div className="container"><Reveal><span className="eyebrow">Begin with one word</span><h2>从今天学会的<br />第一个词开始。</h2><p>把注意力留给学习，其余的交给更合适的节奏。</p><Link className="button button-light" to="/download/"><Download size={17} /> 查看获取方式 <ArrowRight size={17} /></Link></Reveal></div></section></>
}

export default function Home() {
  return <><Hero /><div className="editorial-line container"><span>01 — 理解</span><span>02 — 练习</span><span>03 — 记住</span><div /></div><Features /><Intelligence /><MemoryEngine /><Closing /></>
}


