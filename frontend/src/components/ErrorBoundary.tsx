import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI crash:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[#0F1318] px-4 text-[#D4D8DD]">
          <div className="max-w-lg rounded-lg border border-[#3A4A5A] bg-[#171C23] p-6">
            <p className="text-sm font-medium">Something broke in the UI</p>
            <p className="mt-2 text-xs text-[#3A4A5A]">{this.state.error.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-md border border-[#3A4A5A] px-4 py-2 text-xs hover:border-[#BFA046] hover:text-[#BFA046]"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
