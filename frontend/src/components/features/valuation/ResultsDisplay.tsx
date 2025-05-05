import React from 'react';
import { StockValuationResponse } from '@/types/api'; // Import the type definition

interface ResultsDisplayProps {
  results: StockValuationResponse;
}

// Helper function to format numbers or return 'N/A'
const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return 'N/A';
  }
  return value.toFixed(decimals);
};

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const { stock_info, valuation_results } = results;

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mt-8 space-y-6">
      <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-gray-200 dark:border-gray-700">
        估值结果: {stock_info.name} ({stock_info.ts_code})
      </h2>

      {/* Basic Info Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">行业:</span>
          <span className="ml-2">{stock_info.industry || 'N/A'}</span>
        </div>
        {/* Add more basic info fields if needed */}
      </div>

      {/* Valuation Metrics Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">市盈率 (PE):</span>
          <span className="ml-2">{formatNumber(valuation_results.pe_ratio)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">市净率 (PB):</span>
          <span className="ml-2">{formatNumber(valuation_results.pb_ratio)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">当前股息率 (%):</span>
          <span className="ml-2">{formatNumber(valuation_results.dividend_yield_current)}%</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">股息支付率 (%):</span>
          <span className="ml-2">{formatNumber(valuation_results.dividend_payout_ratio)}%</span>
        </div>
      </div>

      {/* DDM Valuation Section */}
      <div>
        <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-300">股利贴现模型 (DDM)</h3>
        {valuation_results.ddm_valuation && !Array.isArray(valuation_results.ddm_valuation) && valuation_results.ddm_valuation.error ? (
          <p className="text-sm text-red-600 dark:text-red-400">{valuation_results.ddm_valuation.error}</p>
        ) : Array.isArray(valuation_results.ddm_valuation) && valuation_results.ddm_valuation.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                <tr>
                  <th scope="col" className="px-4 py-2">增长率</th>
                  <th scope="col" className="px-4 py-2">折现率</th>
                  <th scope="col" className="px-4 py-2">估值</th>
                  <th scope="col" className="px-4 py-2">溢价率</th>
                </tr>
              </thead>
              <tbody>
                {(valuation_results.ddm_valuation as any[]).map((item, index) => (
                  <tr key={index} className="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                    <td className="px-4 py-2">{formatNumber(item.growth_rate * 100)}%</td>
                    <td className="px-4 py-2">{formatNumber(item.discount_rate * 100)}%</td>
                    <td className="px-4 py-2">{formatNumber(item.value)}</td>
                    <td className={`px-4 py-2 ${item.premium >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {formatNumber(item.premium)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">无 DDM 估值结果。</p>
        )}
      </div>

      {/* Placeholder for other valuation methods */}
      {/* <pre className="text-xs bg-gray-100 dark:bg-gray-700 p-3 rounded overflow-x-auto mt-4">
        {JSON.stringify(valuation_results, null, 2)}
      </pre> */}
    </div>
  );
};

export default ResultsDisplay;
