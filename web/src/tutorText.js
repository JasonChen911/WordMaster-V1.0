export function cleanTutorReply(value) {
  if (typeof value !== 'string') return ''
  return value.replace(/\*\*|__/g, '')
    .replace(/^\s{0,3}#{1,6}\s*/gm, '')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
