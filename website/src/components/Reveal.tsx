import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'

export default function Reveal({ children, className = '', delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduceMotion = useReducedMotion()
  return <motion.div className={className}
    initial={reduceMotion ? false : { opacity: 0, y: 26 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, amount: 0.12 }}
    transition={{ duration: 0.6, delay, ease: [0.22, 0.61, 0.36, 1] }}>
    {children}
  </motion.div>
}
