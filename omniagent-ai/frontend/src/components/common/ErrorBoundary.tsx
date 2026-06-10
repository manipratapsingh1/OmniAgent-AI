import React from "react";
import { FiAlertTriangle, FiRefreshCw } from "react-icons/fi";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, reset: () => void) => React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        this.props.fallback?.(this.state.error, this.reset) || (
          <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-red-500/20 rounded-lg p-6 max-w-md text-center">
              <FiAlertTriangle size={48} className="mx-auto mb-4 text-red-400" />
              <h1 className="text-xl font-bold text-white mb-2">Something went wrong</h1>
              <p className="text-zinc-400 mb-6 text-sm">{this.state.error.message}</p>
              <button
                onClick={this.reset}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition"
              >
                <FiRefreshCw size={16} />
                Try again
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
