// File Analyzer - Analyze uploaded files
import React, { useState } from 'react';
import { Upload, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

interface FileAnalyzerProps {
  onResult: (result: unknown) => void;
}

interface AnalysisResult {
  type?: string;
  lines?: number;
  words?: number;
  characters?: number;
  avg_line_length?: number;
  structure?: unknown;
  rows?: number;
  columns?: number;
  preview?: string[][];
}

const FileAnalyzer = ({ onResult }: FileAnalyzerProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    try {
      setLoading(true);
      setError('');

      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/tools/analyze-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setAnalysis(response.data.result);
      onResult(response.data.result);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* File Upload */}
      <label
        htmlFor="file-analyzer-upload"
        className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-gray-500 transition cursor-pointer relative"
      >
        <input
          id="file-analyzer-upload"
          type="file"
          aria-label="Upload a file for analysis"
          onChange={handleFileChange}
          className="absolute inset-0 opacity-0 cursor-pointer"
        />
        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-300 font-medium">
          {file ? file.name : 'Click to upload or drag and drop'}
        </p>
        <p className="text-xs text-gray-500">
          Supported: TXT, JSON, CSV, PDF, DOCX
        </p>
      </label>

      {/* File Info */}
      {file && (
        <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <p className="text-gray-400">File:</p>
              <p className="text-gray-200 font-mono">{file.name}</p>
            </div>
            <div>
              <p className="text-gray-400">Size:</p>
              <p className="text-gray-200">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
        className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg transition"
      >
        {loading ? 'Analyzing...' : 'Analyze File'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm flex gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-3 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <h3 className="text-sm font-semibold text-gray-200">Analysis Results</h3>

          {/* Text Analysis */}
          {analysis.type === 'text' && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-gray-400">Lines</p>
                <p className="text-2xl font-bold text-blue-400">
                  {analysis.lines}
                </p>
              </div>
              <div>
                <p className="text-gray-400">Words</p>
                <p className="text-2xl font-bold text-blue-400">
                  {analysis.words}
                </p>
              </div>
              <div>
                <p className="text-gray-400">Characters</p>
                <p className="text-2xl font-bold text-blue-400">
                  {analysis.characters}
                </p>
              </div>
              <div>
                <p className="text-gray-400">Avg Length</p>
                <p className="text-lg font-bold text-blue-400">
                  {analysis.avg_line_length?.toFixed(1)}
                </p>
              </div>
            </div>
          )}

          {/* JSON Analysis */}
          {analysis.type === 'json' && (
            <div className="space-y-2">
              <div className="text-xs">
                <p className="text-gray-400">Status: Valid JSON ✓</p>
              </div>
              <div className="text-xs p-2 bg-gray-700 rounded overflow-auto max-h-32">
                <pre className="text-gray-300 whitespace-pre-wrap break-words">
                  {JSON.stringify(analysis.structure, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* CSV Analysis */}
          {analysis.type === 'csv' && (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-gray-400">Rows</p>
                  <p className="text-lg font-bold text-blue-400">
                    {analysis.rows}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Columns</p>
                  <p className="text-lg font-bold text-blue-400">
                    {analysis.columns}
                  </p>
                </div>
              </div>
              {analysis.preview && (
                <div className="text-xs overflow-x-auto">
                  <table className="border-collapse text-gray-300">
                    <tbody>
                      {analysis.preview.slice(0, 5).map((row, i) => (
                        <tr key={i} className="border-b border-gray-600">
                          {row.slice(0, 3).map((cell, j) => (
                            <td key={j} className="px-2 py-1 whitespace-nowrap">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Supported Formats Info */}
      <div className="text-xs text-gray-400 p-3 bg-gray-800/50 rounded-lg border border-gray-700 space-y-1">
        <p>Supported formats:</p>
        <p>• Text: Word count, line count, character analysis</p>
        <p>• JSON: Structure validation & preview</p>
        <p>• CSV: Row/column parsing with data preview</p>
      </div>
    </div>
  );
};

export default FileAnalyzer;
