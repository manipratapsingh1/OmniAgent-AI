// Export & Share Conversations
import React, { useState } from 'react';
import { Download, Share2, Copy, CheckCircle2 } from 'lucide-react';
import axios from 'axios';

interface ExportShareProps {
  conversationId: number;
  onResult: (result: unknown) => void;
}

const ExportShare = ({ conversationId, onResult }: ExportShareProps) => {
  const [exportFormat, setExportFormat] = useState('markdown');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [content, setContent] = useState('');
  const [copied, setCopied] = useState(false);
  const [shareToken, setShareToken] = useState('');
  const [isPublic, setIsPublic] = useState(false);

  const exportFormats = [
    { value: 'markdown', label: 'Markdown (.md)' },
    { value: 'json', label: 'JSON (.json)' },
    { value: 'pdf', label: 'PDF (.pdf)' },
  ];

  const handleExport = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(
        `/api/v1/tools/export-conversation?conv_id=${conversationId}&format=${exportFormat}`
      );

      setContent(response.data.content);
      onResult(response.data);

      // Trigger download
      const element = document.createElement('a');
      element.setAttribute(
        'href',
        `data:text/plain;charset=utf-8,${encodeURIComponent(response.data.content)}`
      );
      element.setAttribute('download', response.data.filename);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Export failed');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(
        `/api/v1/tools/share-conversation?conv_id=${conversationId}`,
        {
          public: isPublic,
        }
      );

      setShareToken(response.data.share_token);
      onResult(response.data);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Sharing failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    const shareUrl = `${window.location.origin}/share/${shareToken}`;
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getFormatPressed = (value: string): boolean =>
    exportFormat === value;

  const publicChecked = isPublic ? 'true' : 'false';

  return (
    <div className="space-y-6">
      {/* Export Section */}
      <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export Conversation
        </h3>

        {/* Format Selection */}
        <div>
          <label className="text-xs font-semibold text-gray-400 block mb-2">
            FORMAT
          </label>
          <div className="grid grid-cols-3 gap-2">
            {exportFormats.map((format) => (
              <button
                key={format.value}
                type="button"
                onClick={() => setExportFormat(format.value)}
                className={`px-2 py-2 rounded text-xs font-medium transition ${
                  exportFormat === format.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {format.label}
              </button>
            ))}
          </div>
        </div>

        {/* Export Button */}
        <button
          type="button"
          onClick={handleExport}
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:opacity-50 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 transition"
        >
          <Download className="w-4 h-4" />
          {loading ? 'Exporting...' : 'Export & Download'}
        </button>

        {/* Preview */}
        {content && (
          <div className="p-3 bg-gray-900 rounded-lg border border-gray-600 max-h-32 overflow-y-auto">
            <p className="text-xs text-gray-400 mb-2">PREVIEW</p>
            <pre className="text-xs text-gray-300 whitespace-pre-wrap break-words font-mono">
              {content.substring(0, 200)}...
            </pre>
          </div>
        )}
      </div>

      {/* Share Section */}
      <div className="space-y-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Share2 className="w-4 h-4" />
          Share Conversation
        </h3>

        {/* Public Toggle */}
        <div className="flex items-center justify-between">
          <label htmlFor="share-public-toggle" className="text-xs font-semibold text-gray-400 flex items-center gap-2">
            Make Public
          </label>
          <button
            type="button"
            id="share-public-toggle"
            onClick={() => setIsPublic(!isPublic)}
            className={`w-12 h-6 rounded-full transition relative ${
              isPublic ? 'bg-green-600' : 'bg-gray-600'
            }`}
            aria-label={isPublic ? 'Disable public sharing' : 'Enable public sharing'}
          >
            <div
              className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition ${
                isPublic ? 'right-0.5' : 'left-0.5'
              }`}
            />
          </button>
        </div>

        {/* Share Button */}
        <button
          type="button"
          onClick={handleShare}
          disabled={loading || Boolean(shareToken)}
          className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-700 hover:to-indigo-600 disabled:opacity-50 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 transition"
        >
          <Share2 className="w-4 h-4" />
          {loading ? 'Generating...' : 'Generate Share Link'}
        </button>

        {/* Share Link Display */}
        {shareToken && (
          <div className="p-3 bg-gray-900 rounded-lg border border-gray-600 space-y-2">
            <p className="text-xs text-gray-400">SHARE LINK</p>
            <div className="flex gap-2">
              <input
                type="text"
                aria-label="Share link"
                value={`${window.location.origin}/share/${shareToken}`}
                readOnly
                className="flex-1 bg-gray-800 text-gray-300 text-xs px-2 py-2 rounded border border-gray-600 font-mono"
              />
              <button
                type="button"
                onClick={handleCopyShareLink}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition flex items-center gap-1"
                aria-label={copied ? 'Share link copied' : 'Copy share link'}
              >
                {copied ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500">
              {isPublic
                ? '🌐 Public - Anyone with the link can view'
                : '🔒 Private - Only authorized users can view'}
            </p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Info */}
      <div className="text-xs text-gray-400 p-3 bg-gray-800/50 rounded-lg border border-gray-700 space-y-1">
        <p>✓ Markdown: Clean, readable format for sharing</p>
        <p>✓ JSON: Structured data for integration</p>
        <p>✓ PDF: Professional format for printing</p>
        <p>✓ Sharing: Secure token-based access</p>
      </div>
    </div>
  );
};

export default ExportShare;
