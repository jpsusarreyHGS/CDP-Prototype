import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Log script errors specifically
    if (error.message === 'Script error.' || error.name === 'ScriptError') {
      console.error('Script error detected - this is often a cross-origin error. Check:');
      console.error('1. CORS headers on the MFE server');
      console.error('2. Network tab for failed requests');
      console.error('3. MFE component for runtime errors');
    }
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isScriptError = this.state.error?.message === 'Script error.' || this.state.error?.name === 'ScriptError';
      
      return (
        <div style={{ padding: '20px', border: '2px solid #f44336', borderRadius: '4px', background: '#ffebee' }}>
          <h3 style={{ color: '#d32f2f', margin: '0 0 10px 0' }}>Something went wrong</h3>
          {isScriptError ? (
            <>
              <p style={{ color: '#c62828', margin: '0 0 10px 0', fontWeight: 'bold' }}>
                Script Error Detected
              </p>
              <p style={{ color: '#666', margin: '0 0 10px 0', fontSize: '0.9em' }}>
                This is typically a cross-origin error. The MFE component may have thrown an error, but details are hidden for security.
              </p>
              <ul style={{ color: '#666', margin: '0 0 10px 0', fontSize: '0.9em', paddingLeft: '20px' }}>
                <li>Check the browser console for more details</li>
                <li>Verify CORS headers on your MFE server (port 8027)</li>
                <li>Check the Network tab for failed requests</li>
                <li>Ensure the MFE component is working when accessed directly</li>
              </ul>
            </>
          ) : (
            <p style={{ color: '#c62828', margin: '0 0 10px 0' }}>
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
          )}
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '8px 16px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            Try Again
          </button>
          {isScriptError && (
            <button
              onClick={() => {
                window.open('http://localhost:8027', '_blank');
              }}
              style={{
                padding: '8px 16px',
                background: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Open MFE Directly
            </button>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

