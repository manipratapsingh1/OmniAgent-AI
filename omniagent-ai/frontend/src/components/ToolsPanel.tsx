// Advanced Tools Panel - ChatGPT/Gemini style tools
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Code2,
  Calculator,
  FileText,
  BarChart3,
  Download,
  Share2,
  X,
} from 'lucide-react';
import CodeEditor from './CodeEditor';
import CalculatorTool from './CalculatorTool';
import FileAnalyzer from './FileAnalyzer';
import DataVisualizer from './DataVisualizer';
import ExportShare from './ExportShare';

interface ToolsPanelProps {
  conversationId: number;
  visible: boolean;
  onClose: () => void;
}

const ToolsPanel = ({ conversationId, visible, onClose }: ToolsPanelProps) => {
  const [activeTab, setActiveTab] = useState('code');
  const [toolResults, setToolResults] = useState<Record<string, unknown>>({});

  const tools = [
    {
      id: 'code',
      name: 'Code Interpreter',
      icon: Code2,
      description: 'Execute Python code safely',
      color: 'from-purple-500 to-pink-500',
    },
    {
      id: 'calculator',
      name: 'Calculator',
      icon: Calculator,
      description: 'Advanced mathematical expressions',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      id: 'file',
      name: 'File Analyzer',
      icon: FileText,
      description: 'Analyze uploaded files',
      color: 'from-orange-500 to-red-500',
    },
    {
      id: 'visualize',
      name: 'Data Visualizer',
      icon: BarChart3,
      description: 'Generate charts & graphs',
      color: 'from-green-500 to-emerald-500',
    },
    {
      id: 'export',
      name: 'Export & Share',
      icon: Share2,
      description: 'Share conversations',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  if (!visible) return null;

  const handleToolResult = (toolId: string, result: unknown) => {
    setToolResults((prev) => ({
      ...prev,
      [toolId]: result,
    }));
  };

  const renderToolContent = () => {
    switch (activeTab) {
      case 'code':
        return (
          <CodeEditor
            onResult={(result) => handleToolResult('code', result)}
          />
        );
      case 'calculator':
        return (
          <CalculatorTool
            onResult={(result) => handleToolResult('calculator', result)}
          />
        );
      case 'file':
        return (
          <FileAnalyzer
            onResult={(result) => handleToolResult('file', result)}
          />
        );
      case 'visualize':
        return (
          <DataVisualizer
            onResult={(result) => handleToolResult('visualize', result)}
          />
        );
      case 'export':
        return (
          <ExportShare
            conversationId={conversationId}
            onResult={(result) => handleToolResult('export', result)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 400 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 400 }}
        className="fixed top-0 right-0 h-full w-96 bg-gradient-to-b from-gray-900 to-gray-800 border-l border-gray-700 shadow-2xl z-50 overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Code2 className="w-5 h-5" />
            Advanced Tools
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close advanced tools panel"
            className="p-1 hover:bg-gray-700 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tool Tabs */}
        <div className="flex gap-2 p-4 border-b border-gray-700 overflow-x-auto">
          {tools.map((tool) => {
            const Icon = tool.icon;
            return (
              <motion.button
                key={tool.id}
                type="button"
                onClick={() => setActiveTab(tool.id)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                aria-pressed={activeTab === tool.id}
                aria-label={`Switch to ${tool.name}`}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg transition whitespace-nowrap ${
                  activeTab === tool.id
                    ? `bg-gradient-to-r ${tool.color} text-white`
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-xs font-medium">{tool.name}</span>
              </motion.button>
            );
          })}
        </div>

        {/* Tool Content */}
        <div className="p-4">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {renderToolContent()}
          </motion.div>
        </div>

        {/* Results Display */}
        {toolResults[activeTab] !== undefined && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mx-4 mb-4 p-4 bg-gray-700 rounded-lg border border-gray-600"
          >
            <p className="text-xs font-semibold text-gray-400 mb-2">RESULT</p>
            <pre className="text-xs text-gray-300 overflow-auto max-h-48 whitespace-pre-wrap break-words">
              {JSON.stringify(toolResults[activeTab], null, 2)}
            </pre>
          </motion.div>
        )}
      </motion.div>

      {/* Overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        aria-hidden="true"
        className="fixed inset-0 bg-black/50 z-40"
      />
    </AnimatePresence>
  );
};

export default ToolsPanel;
