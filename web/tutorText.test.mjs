import test from 'node:test'
import assert from 'node:assert/strict'
import { cleanTutorReply } from './src/tutorText.js'

test('tutor reply removes markdown noise and keeps the actual advice', () => {
  assert.equal(cleanTutorReply('## 听力\n\n**重点**\n- 每天练一套真题'), '听力\n\n重点\n• 每天练一套真题')
})
