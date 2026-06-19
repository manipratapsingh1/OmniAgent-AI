// Advanced Calculator with scientific functions
import React, { useState } from 'react';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { RotateCcw, Copy } from 'lucide-react';
import { api } from '../api/client';

interface CalculatorToolProps {
  onResult: (result: unknown) => void;
}

interface HistoryEntry {
  expr: string;
  result: string | number;
}

const CalculatorTool = ({ onResult }: CalculatorToolProps) => {
  const [expression, setExpression] = useState('');
  const [result, setResult] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const handleCalculate = async () => {
    if (!expression.trim()) return;

    try {
      const response = await api.post('/tools/calculate', {
        expression,
      });

      const data = response.data;
      setResult(data.result);
      setHistory((prev) => [
        ...prev,
        { expr: expression, result: data.result },
      ]);
      onResult(data);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setResult('Error: ' + (axiosErr.response?.data?.detail || 'Invalid expression'));
    }
  };

  const buttons = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['0', '.', '=', '+'],
  ];

  const handleButtonClick = (btn: string) => {
    if (btn === '=') {
      handleCalculate();
    } else if (btn === 'C') {
      setExpression('');
      setResult('');
    } else {
      setExpression((prev) => prev + btn);
    }
  };

  const scientificFunctions = [
    { name: 'sqrt(x)', label: '√' },
    { name: 'sin(x)', label: 'sin' },
    { name: 'cos(x)', label: 'cos' },
    { name: 'tan(x)', label: 'tan' },
    { name: 'log(x)', label: 'log' },
    { name: 'ln(x)', label: 'ln' },
    { name: 'exp(x)', label: 'e^x' },
    { name: 'abs(x)', label: '|x|' },
  ];

  const insertFunction = (func: string) => {
    const newExpr = expression + func + '(';
    setExpression(newExpr);
  };

  return (
    <div className="space-y-4">
      {/* Display */}
      <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
        <input
          type="text"
          value={expression}
          onChange={(e) => setExpression(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCalculate()}
          className="w-full bg-transparent text-right text-2xl text-white font-mono focus:outline-none mb-2"
          placeholder="0"
        />
        {result && (
          <div className="text-right text-lg text-blue-400 font-semibold">
            = {result}
          </div>
        )}
      </div>

      {/* Scientific Functions */}
      <div className="grid grid-cols-4 gap-2">
        {scientificFunctions.map((func) => (
          <button
            key={func.name}
            onClick={() => insertFunction(func.name)}
            className="bg-blue-900 hover:bg-blue-800 text-blue-200 px-2 py-2 rounded text-xs font-semibold transition"
          >
            {func.label}
          </button>
        ))}
      </div>
      {/* Calculator Buttons */}
      <div className="grid grid-cols-4 gap-2">
        {buttons.map((row) =>
          row.map((btn) => (
            <button
              key={btn}
              onClick={() => handleButtonClick(btn)}
              className={`py-3 rounded-lg font-semibold transition ${
                btn === '='
                  ? 'col-span-1 bg-green-600 hover:bg-green-700 text-white'
                  : ['+', '-', '*', '/'].includes(btn)
                  ? 'bg-orange-600 hover:bg-orange-700 text-white'
                  : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
            >
              {btn}
            </button>
          ))
        )}
      </div>

      {/* Clear and History Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => {
            setExpression('');
            setResult('');
          }}
          className="flex-1 bg-red-900 hover:bg-red-800 text-white py-2 rounded-lg flex items-center justify-center gap-2 transition"
        >
          <RotateCcw className="w-4 h-4" />
          Clear
        </button>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
          <p className="text-xs font-semibold text-gray-400 mb-2">HISTORY</p>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {history.slice().reverse().map((item, i) => (
              <div key={i} className="text-xs text-gray-300 flex justify-between">
                <span>{item.expr}</span>
                <span className="text-blue-400 font-semibold">{item.result}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Examples */}
      <div className="text-xs text-gray-400 p-3 bg-gray-800/50 rounded-lg border border-gray-700 space-y-1">
        <p>Examples:</p>
        <p>• sin(3.14159) / 2</p>
        <p>• sqrt(16) + pow(2, 3)</p>
        <p>• log(100) - abs(-5)</p>
      </div>
    </div>
  );
};

export default CalculatorTool;
