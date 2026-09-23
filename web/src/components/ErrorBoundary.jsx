import React from 'react'
import ErrorFallback from './ErrorFallback'

/**
 * ErrorBoundary — catches render errors anywhere in the child tree.
 * Prevents a single component error from white-screening the entire app.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <App />
 *   </ErrorBoundary>
 *
 * Per-route granularity is also supported:
 *   <ErrorBoundary><StudyPage /></ErrorBoundary>
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    // Log to console for debugging; in production this could go to a telemetry service.
    console.error(
      '[ErrorBoundary] React render error caught:\n',
      error,
      '\nComponent stack:\n',
      errorInfo?.componentStack ?? '(unavailable)',
    )
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      // Allow caller to supply a custom fallback render-prop style
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(this.state.error, this.handleReset)
      }
      return <ErrorFallback error={this.state.error} onReset={this.handleReset} />
    }

    return this.props.children
  }
}
