import readingRoom from '../assets/backgrounds/reading-room.webp'
import mistyMountains from '../assets/backgrounds/misty-mountains.webp'
import quietCoast from '../assets/backgrounds/quiet-coast.webp'

export const BACKGROUNDS = [
  { id: 'reading-room', name: '暖色书房', url: readingRoom },
  { id: 'misty-mountains', name: '晨雾山景', url: mistyMountains },
  { id: 'quiet-coast', name: '安静海岸', url: quietCoast },
]

export function getBackground(id) {
  return BACKGROUNDS.find((background) => background.id === id) || null
}

export function backgroundImageFor(background, isDark) {
  if (!background) return 'none'
  const tint = isDark ? 'rgba(6, 12, 22, 0.68)' : 'rgba(255, 255, 255, 0.58)'
  return `linear-gradient(${tint}, ${tint}), url("${background.url}")`
}
