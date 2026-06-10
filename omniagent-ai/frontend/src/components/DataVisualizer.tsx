// Data Visualizer - Generate beautiful charts
import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';
import axios from 'axios';

interface DataVisualizerProps {
  onResult: (result: unknown) => void;
}

interface ChartConfig {
  chart_type?: string;
  data?: unknown[];
  statistics?: Record<string, number>;
}

const DataVisualizer = ({ onResult }: DataVisualizerProps) => {
  const [chartType, setChartType] = useState('line');
  const [dataInput, setDataInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [chartConfig, setChartConfig] = useState<ChartConfig | null>(null);

  const chartTypes = [
    { value: 'line', label: 'Line Chart' },
    { value: 'bar', label: 'Bar Chart' },
    { value: 'pie', label: 'Pie Chart' },
    { value: 'area', label: 'Area Chart' },
    { value: 'scatter', label: 'Scatter Plot' },
  ];

  const examples = [
    {
      name: 'Sales Data',
      data: JSON.stringify([
        { month: 'Jan', sales: 4000, profit: 2400 },
        { month: 'Feb', sales: 3000, profit: 1398 },
        { month: 'Mar', sales: 2000, profit: 9800 },
        { month: 'Apr', sales: 2780, profit: 3908 },
      ]),
    },
    {
      name: 'Website Stats',
      data: JSON.stringify([
        { day: 'Mon', visits: 1200 },
        { day: 'Tue', visits: 1900 },
        { day: 'Wed', visits: 1600 },
        { day: 'Thu', visits: 2200 },
        { day: 'Fri', visits: 2800 },
      ]),
    },
    {
      name: 'Distribution',
      data: JSON.stringify([
        { category: 'A', value: 30 },
        { category: 'B', value: 25 },
        { category: 'C', value: 20 },
        { category: 'D', value: 25 },
      ]),
    },
  ];

  const handleGenerateChart = async () => {
    try {
      const data = JSON.parse(dataInput);
      setLoading(true);
      setError('');

      const response = await axios.post('/api/v1/tools/generate-chart', {
        data,
        chart_type: chartType,
      });

      setChartConfig(response.data.result);
      onResult(response.data.result);
    } catch (err: unknown) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format');
      } else {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Chart generation failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadExample = (example: { data: string }) => {
    setDataInput(example.data);
  };

  return (
    <div className="space-y-4">
      {/* Chart Type Selection */}
      <div>
        <p className="text-xs font-semibold text-gray-400 block mb-2">
          CHART TYPE
        </p>
        <div className="grid grid-cols-2 gap-2">
          {chartTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setChartType(type.value)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                chartType === type.value
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Examples */}
      <div>
        <p className="text-xs font-semibold text-gray-400 block mb-2">
          QUICK EXAMPLES
        </p>
        <div className="flex gap-2 flex-wrap">
          {examples.map((example) => (
            <button
              key={example.name}
              onClick={() => loadExample(example)}
              className="text-xs px-3 py-1 rounded-full bg-green-900 text-green-200 hover:bg-green-800 transition"
            >
              {example.name}
            </button>
          ))}
        </div>
      </div>

      {/* Data Input */}
      <div>
        <p className="text-xs font-semibold text-gray-400 block mb-2">
          DATA (JSON FORMAT)
        </p>
        <textarea
          value={dataInput}
          onChange={(e) => setDataInput(e.target.value)}
          className="w-full h-40 bg-gray-800 text-gray-100 p-3 rounded-lg font-mono text-sm border border-gray-700 focus:border-green-500 focus:outline-none"
          placeholder='[{"x": 1, "y": 10}, {"x": 2, "y": 20}]'
        />
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerateChart}
        disabled={loading || !dataInput.trim()}
        className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg transition"
      >
        {loading ? 'Generating...' : 'Generate Chart'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm flex gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Chart Config Preview */}
      {chartConfig && (
        <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
          <p className="text-xs font-semibold text-gray-400 mb-2">
            CHART CONFIGURATION
          </p>
          <div className="space-y-2 text-xs text-gray-300">
            <div className="flex justify-between">
              <span className="text-gray-500">Type:</span>
              <span className="font-mono">{chartConfig.chart_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Points:</span>
              <span className="font-mono">{chartConfig.data?.length || 0}</span>
            </div>
            {chartConfig.statistics && (
              <div>
                <p className="text-gray-500 mb-1">Statistics:</p>
                <div className="pl-2 space-y-1 text-gray-400">
                  {Object.entries(chartConfig.statistics).map(
                    ([key, value]: [string, unknown]) => (
                      <div key={key} className="flex justify-between">
                        <span>{key}:</span>
                        <span className="font-mono">
                          {typeof value === 'number'
                            ? value.toFixed(2)
                            : String(value)}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Info */}
      <div className="text-xs text-gray-400 p-3 bg-gray-800/50 rounded-lg border border-gray-700 space-y-1">
        <p>Data format examples:</p>
        <p>• Line/Bar: {`[{"label": "A", "value": 10}]`}</p>
        <p>• Multi-series: {`[{"x": "Jan", "sales": 100, "profit": 50}]`}</p>
        <p>• Pie: {`[{"name": "A", "value": 30}]`}</p>
      </div>
    </div>
  );
};

export default DataVisualizer;
