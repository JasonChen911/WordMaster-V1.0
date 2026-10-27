/* Runs before the module entry, including when that entry itself cannot load. */
;(function () {
  var build = document.querySelector('meta[name="wordmaster-build"]')?.content || 'unknown'
  var key = 'dynamic-import-reload-v1:' + build
  var pending = false
  function isChunkError(error) {
    return /Failed to fetch dynamically imported module|Importing a module script failed|ChunkLoadError|Loading chunk .* failed|Unable to preload CSS for/i.test(error?.message || String(error || ''))
  }
  function log(event, error) {
    var asset = String(error?.message || '').match(/\/assets\/([A-Za-z0-9_-]+\.(?:js|css))/)?.[1] || ''
    var payload = { event: event, build: build, asset: asset }
    console.error('[Frontend]', JSON.stringify(payload))
    fetch('/api/frontend/log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), keepalive: true }).catch(function () {})
  }
  function showEntryFailure(recovering) {
    var root = document.getElementById('root')
    if (!root || root.hasChildNodes()) return
    document.getElementById('splash')?.remove()
    root.innerHTML = '<div style="padding:48px;text-align:center"><h2>页面出现了问题</h2><p>' +
      (recovering ? '界面资源更新后加载失败，WordMaster 正在尝试自动恢复。' : '界面资源自动恢复失败，请刷新页面或回首页。') +
      '</p>' + (recovering ? '' : '<button onclick="location.reload()">刷新页面</button> <a href="/">回首页</a>') + '</div>'
  }
  function recover(error) {
    if (!isChunkError(error)) return false
    if (pending) return true
    log('dynamic_import', error)
    try {
      if (sessionStorage.getItem(key)) { log('recovery_failed', error); return false }
      // Set BEFORE reloading; never clear on mount/success, so repeated failures stop.
      sessionStorage.setItem(key, '1')
    } catch (_) { log('recovery_failed', error); return false }
    pending = true
    log('auto_reload', error)
    setTimeout(function () {
      var url = new URL(window.location.href)
      url.searchParams.set('wm-build', build)
      url.searchParams.set('wm-recover', '1')
      // HTML/bootstrap are no-store. A new navigation also clears the module map
      // and React.lazy's cached rejection; learning/localStorage data is untouched.
      window.location.replace(url.href)
    }, 80)
    return true
  }
  window.wordmasterRecovery = { recover: recover, isChunkError: isChunkError }
  window.addEventListener('vite:preloadError', function (event) {
    // Keep Vite's original rejection so React.lazy receives the real error,
    // not an undefined module (preventDefault would swallow that rejection).
    recover(event.payload)
  })
  window.addEventListener('unhandledrejection', function (event) {
    if (!isChunkError(event.reason)) return
    var retrying = recover(event.reason)
    if (retrying) event.preventDefault()
    showEntryFailure(retrying)
  })
  window.addEventListener('error', function (event) {
    if (isChunkError(event.error || event.message)) {
      showEntryFailure(recover(event.error || new Error(event.message)))
      return
    }
    var src = event.target?.src || ''
    if (event.target?.tagName === 'SCRIPT' && /\/assets\/[^/]+\.js/.test(src)) {
      var error = new Error('Failed to fetch dynamically imported module: ' + src)
      log('entry_load_failed', error)
      showEntryFailure(recover(error))
    }
  }, true)
})()
