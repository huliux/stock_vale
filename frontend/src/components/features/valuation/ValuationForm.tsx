"use client";

import React, { useState } from 'react';

interface ValuationFormProps {
  onSubmit: (tsCode: string) => void; // Callback function to trigger valuation
  isLoading: boolean;
}

const ValuationForm: React.FC<ValuationFormProps> = ({ onSubmit, isLoading }) => {
  const [tsCode, setTsCode] = useState<string>('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (tsCode.trim()) {
      onSubmit(tsCode.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="tsCode" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          股票代码 (例如: 000001.SZ)
        </label>
        <input
          type="text"
          id="tsCode"
          value={tsCode}
          onChange={(e) => setTsCode(e.target.value)}
          placeholder="输入股票代码"
          required
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          disabled={isLoading}
        />
      </div>
      <button
        type="submit"
        disabled={isLoading || !tsCode.trim()}
        className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? '正在计算...' : '获取估值'}
      </button>
    </form>
  );
};

export default ValuationForm;
