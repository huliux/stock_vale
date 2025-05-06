import React from 'react';
import {
  StockValuationResponse,
  ValuationContainer,
  SensitivityResult,
  ComboValuationItem,
  InvestmentAdvice,
  OtherAnalysisContainer,
  ValuationResultsContainer,
  StockInfo
} from '@/types/api'; // Import updated types

interface ResultsDisplayProps {
  results: StockValuationResponse | null; // Allow null results
}

// Helper function to format numbers or return 'N/A'
const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return 'N/A';
  }
  return value.toFixed(decimals);
};

// Helper function to format percentage
const formatPercent = (value: number | null | undefined, decimals: number = 1): string => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return 'N/A';
  }
  return `${value.toFixed(decimals)}%`;
};

// Helper component to render sensitivity tables for DCF/DDM
const SensitivityTable: React.FC<{ data: SensitivityResult[] | null | undefined, title: string }> = ({ data, title }) => {
  if (!data || data.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">无 {title} 估值结果。</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm text-left text-gray-500 dark:text-gray-400">
        <caption className="caption-top text-base font-medium mb-1 text-gray-600 dark:text-gray-400">{title} 敏感性分析</caption>
        <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            <th scope="col" className="px-4 py-2">增长率</th>
            <th scope="col" className="px-4 py-2">折现率</th>
            <th scope="col" className="px-4 py-2">估值</th>
            <th scope="col" className="px-4 py-2">溢价率</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr key={index} className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
              <td className="px-4 py-2">{formatPercent(item.growth_rate ? item.growth_rate * 100 : null)}</td>
              <td className="px-4 py-2">{formatPercent(item.discount_rate ? item.discount_rate * 100 : null)}</td>
              <td className="px-4 py-2">{formatNumber(item.value)}</td>
              <td className={`px-4 py-2 ${item.premium !== null && item.premium !== undefined && item.premium >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {formatPercent(item.premium)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Helper component to render valuation containers (DCF/DDM)
const ValuationSection: React.FC<{ container: ValuationContainer | null | undefined, title: string }> = ({ container, title }) => {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-300">{title}</h3>
      {container?.error_message ? (
        <p className="text-sm text-red-600 dark:text-red-400">{container.error_message}</p>
      ) : (
        <SensitivityTable data={container?.results} title={title} />
      )}
    </div>
  );
};


const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  // Handle null results case
  if (!results || !results.stock_info || !results.valuation_results) {
    // Optionally render a loading state or message if results are null initially
    return null; // Or a placeholder component
  }

  const { stock_info, valuation_results } = results;

  // Safely access nested properties
  const dividendAnalysis = valuation_results.other_analysis?.dividend_analysis;
  const growthAnalysis = valuation_results.other_analysis?.growth_analysis;
  const comboValuations = valuation_results.combo_valuations;
  const investmentAdvice = valuation_results.investment_advice;

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mt-8 space-y-8"> {/* Increased spacing */}
      <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-gray-200 dark:border-gray-700">
        估值结果: {stock_info.name} ({stock_info.ts_code})
      </h2>

      {/* Basic Info & Key Metrics Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4"> {/* Adjusted grid for more items */}
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">行业:</span>
          <span className="ml-2">{stock_info.industry || 'N/A'}</span>
        </div>
         <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">最新价格:</span>
          <span className="ml-2 font-semibold">{formatNumber(valuation_results.latest_price)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">市盈率 (PE):</span>
          <span className="ml-2">{formatNumber(valuation_results.current_pe)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">市净率 (PB):</span>
          <span className="ml-2">{formatNumber(valuation_results.current_pb)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">EV/EBITDA:</span>
          <span className="ml-2">{formatNumber(valuation_results.current_ev_ebitda)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">WACC (%):</span>
          <span className="ml-2">{formatPercent(valuation_results.calculated_wacc_pct)}</span>
        </div>
        <div>
          <span className="font-medium text-gray-600 dark:text-gray-400">股权成本 Ke (%):</span>
          <span className="ml-2">{formatPercent(valuation_results.calculated_cost_of_equity_pct)}</span>
        </div>
      </div>

      {/* Other Analysis Section */}
      <div>
        <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-300">其他分析</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded">
          {/* Dividend Analysis */}
          <div>
            <h4 className="font-medium mb-1 text-gray-600 dark:text-gray-400">股息分析:</h4>
            <ul className="list-disc list-inside text-sm space-y-1">
              <li>当前股息率: {formatPercent(dividendAnalysis?.current_yield_pct)}</li>
              <li>近3年平均股息: {formatNumber(dividendAnalysis?.avg_dividend_3y)}</li>
              <li>股息支付率: {formatPercent(dividendAnalysis?.payout_ratio_pct)}</li>
            </ul>
          </div>
          {/* Growth Analysis */}
          <div>
            <h4 className="font-medium mb-1 text-gray-600 dark:text-gray-400">增长分析:</h4>
            <ul className="list-disc list-inside text-sm space-y-1">
              <li>净利润3年CAGR: {formatPercent(growthAnalysis?.net_income_cagr_3y)}</li>
              <li>营收3年CAGR: {formatPercent(growthAnalysis?.revenue_cagr_3y)}</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Investment Advice Section */}
      {investmentAdvice && (
        <div className="p-4 border border-blue-200 dark:border-blue-700 rounded bg-blue-50 dark:bg-gray-700">
          <h3 className="text-lg font-semibold mb-2 text-blue-800 dark:text-blue-300">投资建议</h3>
          <p className="text-xl font-bold mb-2">
            建议: <span className={`
              ${investmentAdvice.advice?.includes('买入') ? 'text-green-600 dark:text-green-400' : ''}
              ${investmentAdvice.advice?.includes('卖出') ? 'text-red-600 dark:text-red-400' : ''}
              ${investmentAdvice.advice?.includes('持有') || investmentAdvice.advice?.includes('观察') || investmentAdvice.advice?.includes('无法') ? 'text-yellow-600 dark:text-yellow-400' : ''}
            `}>
              {investmentAdvice.advice || 'N/A'}
            </span>
          </p>
          <p className="text-sm mb-1"><span className="font-medium">依据:</span> {investmentAdvice.based_on || 'N/A'}</p>
          <p className="text-sm mb-1"><span className="font-medium">理由:</span> {investmentAdvice.reason || 'N/A'}</p>
          <p className="text-sm mb-1">
            <span className="font-medium">估值区间 (基于FCFE Basic & DDM):</span> {formatNumber(investmentAdvice.min_intrinsic_value)} - {formatNumber(investmentAdvice.max_intrinsic_value)}
            <span className="font-medium ml-4">平均值:</span> {formatNumber(investmentAdvice.avg_intrinsic_value)}
          </p>
          <p className="text-sm mb-1">
            <span className="font-medium">安全边际 (基于下限):</span>
            <span className={`ml-1 ${investmentAdvice.safety_margin_pct !== null && investmentAdvice.safety_margin_pct !== undefined && investmentAdvice.safety_margin_pct >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {formatPercent(investmentAdvice.safety_margin_pct)}
            </span>
          </p>
          <p className="text-xs mt-2 text-gray-500 dark:text-gray-400"><span className="font-medium">参考信息:</span> {investmentAdvice.reference_info || 'N/A'}</p>
        </div>
      )}

      {/* Combo Valuations Section */}
      {comboValuations && Object.keys(comboValuations).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-300">组合估值</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(comboValuations)
              .sort(([keyA], [keyB]) => keyA.localeCompare(keyB)) // Sort alphabetically by key
              .map(([key, item]) => (
              <div key={key} className="p-3 border rounded bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
                <p className="font-medium text-sm text-gray-800 dark:text-gray-200">{key}:</p>
                {item ? (
                  <>
                    <p className="text-lg font-semibold">{formatNumber(item.value)}</p>
                    <p className={`text-xs ${item.safety_margin_pct !== null && item.safety_margin_pct !== undefined && item.safety_margin_pct >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      安全边际: {formatPercent(item.safety_margin_pct)}
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">N/A</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}


      {/* DCF Valuations Section */}
      <ValuationSection container={valuation_results.dcf_fcff_basic_capex} title="DCF - FCFF (基本 Capex)" />
      <ValuationSection container={valuation_results.dcf_fcfe_basic_capex} title="DCF - FCFE (基本 Capex)" />
      <ValuationSection container={valuation_results.dcf_fcff_full_capex} title="DCF - FCFF (完整 Capex)" />
      <ValuationSection container={valuation_results.dcf_fcfe_full_capex} title="DCF - FCFE (完整 Capex)" />

      {/* DDM Valuation Section - Updated */}
      <ValuationSection container={valuation_results.ddm} title="股利贴现模型 (DDM)" />


      {/* Optional: Raw JSON for debugging */}
      {/* <details className="mt-6">
        <summary className="text-sm cursor-pointer text-gray-500 dark:text-gray-400">查看原始 JSON 数据</summary>
        <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-3 rounded overflow-x-auto mt-2 border dark:border-gray-700">
          {JSON.stringify(results, null, 2)}
        </pre>
      </details> */}
    </div>
  );
};

export default ResultsDisplay;
