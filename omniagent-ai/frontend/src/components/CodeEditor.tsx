// Code Interpreter - Execute Python code safely
import React, { useState } from 'react';
import { Play, Copy, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface CodeEditorProps {
  onResult: (result: unknown) => void;
}

const CodeEditor = ({ onResult }: CodeEditorProps) => {
  const [code, setCode] = useState('# Write Python code here\nresult = 2 + 2\nprint(result)');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [output, setOutput] = useState('');

  const handleExecute = async () => {
    try {
      setLoading(true);
      setError('');
      setOutput('');

      const response = await axios.post('/api/v1/tools/execute-code', {
        code,
      });

      if (response.data.success) {
        setOutput(JSON.stringify(response.data.result, null, 2));
        onResult(response.data.result);
      } else {
        setError(response.data.error || 'Execution failed');
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Error executing code');
    } finally {
      setLoading(false);
    }
  };

  const examples = [
    {
      name: 'Math',
      code: 'import math\nresult = math.sqrt(16) + math.pi',
    },
    {
      name: 'Lists',
      code: 'data = [1, 2, 3, 4, 5]\nresult = sum(data) / len(data)',
    },
    {
      name: 'JSON',
      code: 'import json\ndata = {"name": "AI", "version": 2}\nresult = json.dumps(data)',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Examples */}
      <div className="flex gap-2 flex-wrap">
        {examples.map((example) => (
          <button
            key={example.name}
            onClick={() => setCode(example.code)}
            className="text-xs px-3 py-1 rounded-full bg-purple-900 text-purple-200 hover:bg-purple-800 transition"
          >
            {example.name}
          </button>
        ))}
      </div>

      {/* Code Editor */}
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        className="w-full h-48 bg-gray-800 text-gray-100 p-3 rounded-lg font-mono text-sm border border-gray-700 focus:border-purple-500 focus:outline-none"
        placeholder="Write Python code here..."
      />

      {/* Execute Button */}
      <button
        onClick={handleExecute}
        disabled={loading || !code.trim()}
        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 transition"
      >
        <Play className="w-4 h-4" />
        {loading ? 'Executing...' : 'Execute'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm flex gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Output Display */}
      {output && (
        <div className="p-3 bg-gray-700/50 border border-gray-600 rounded-lg">
          <p className="text-xs font-semibold text-gray-400 mb-2">OUTPUT</p>
          <pre className="text-xs text-gray-200 overflow-auto max-h-32 whitespace-pre-wrap break-words font-mono">
            {output}
          </pre>
        </div>
      )}

      {/* Info */}
      <div className="text-xs text-gray-400 p-3 bg-gray-800/50 rounded-lg border border-gray-700">
        <p>✓ Supports: math, json, datetime, statistics, collections</p>
        <p>✗ Cannot import: os, sys, subprocess, socket, requests</p>
      </div>
    </div>
  );
};

export default CodeEditor;
