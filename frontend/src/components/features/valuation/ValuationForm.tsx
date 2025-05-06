"use client";

import React, { useState } from 'react';

// Define an interface for the form state including WACC params
interface FormData {
  tsCode: string; // This will now be constructed before submitting
  targetDebtRatio: string;
  costOfDebt: string;
  taxRate: string;
  riskFreeRate: string;
  beta: string;
  marketRiskPremium: string;
  sizePremium: string;
}

interface ValuationFormProps {
  onSubmit: (formData: FormData) => void; // onSubmit still expects the final FormData
  isLoading: boolean;
}

// Helper component for input fields (remains the same)
const InputField: React.FC<{
  id: keyof FormData | 'numericCode'; // Allow numericCode id
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  type?: string;
  step?: string;
  required?: boolean;
  disabled?: boolean;
  unit?: string;
}> = ({ id, label, value, onChange, placeholder, type = "text", step, required = false, disabled = false, unit }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
      {label} {unit && `(${unit})`}
    </label>
    <div className="relative">
      <input
        type={type}
        id={id}
        name={id}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        step={step}
        required={required}
        disabled={disabled}
        className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${unit ? 'pr-8' : ''}`}
      />
      {unit && (
        <span className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm text-gray-500 dark:text-gray-400">
          {unit}
        </span>
      )}
    </div>
  </div>
);


const ValuationForm: React.FC<ValuationFormProps> = ({ onSubmit, isLoading }) => {
  // Separate state for numeric code and suffix
  const [numericCode, setNumericCode] = useState<string>('');
  const [marketSuffix, setMarketSuffix] = useState<'.SH' | '.SZ'>('.SH'); // Default to .SH

  const [waccParams, setWaccParams] = useState({
    targetDebtRatio: '45.0',
    costOfDebt: '5.0',
    taxRate: '25.0',
    riskFreeRate: '3.0',
    beta: '1.33',
    marketRiskPremium: '6.11',
    sizePremium: '0.0',
  });

  const handleNumericCodeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    // Allow only digits
    const value = event.target.value.replace(/\D/g, '');
    setNumericCode(value);
  };

  const handleWaccChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setWaccParams(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedNumericCode = numericCode.trim();
    if (trimmedNumericCode) {
      const fullTsCode = `${trimmedNumericCode}${marketSuffix}`;
      const formData: FormData = {
        tsCode: fullTsCode,
        ...waccParams, // Include WACC parameters
      };
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
       <h2 className="text-xl font-semibold mb-4 border-b pb-2 border-gray-200 dark:border-gray-700">输入参数</h2>

      {/* Stock Code Input with Suffix Buttons */}
      <div>
        <label htmlFor="numericCode" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          股票代码 (仅数字)
        </label>
        <div className="flex items-center space-x-2">
          <input
            type="text" // Use text to allow leading zeros if needed, or tel
            id="numericCode"
            name="numericCode"
            value={numericCode}
            onChange={handleNumericCodeChange}
            placeholder="例如: 600519"
            required
            className="flex-grow px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            disabled={isLoading}
            pattern="\d*" // Suggest numeric input but allow text for flexibility
          />
          <div className="flex rounded-md shadow-sm">
            <button
              type="button"
              onClick={() => setMarketSuffix('.SH')}
              disabled={isLoading}
              className={`px-3 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 ${
                marketSuffix === '.SH'
                  ? 'bg-indigo-600 text-white dark:bg-indigo-500'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              .SH
            </button>
            <button
              type="button"
              onClick={() => setMarketSuffix('.SZ')}
              disabled={isLoading}
              className={`-ml-px px-3 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 ${
                marketSuffix === '.SZ'
                  ? 'bg-indigo-600 text-white dark:bg-indigo-500'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              .SZ
            </button>
          </div>
        </div>
      </div>


      {/* WACC Configuration Section */}
      <details className="space-y-4 border dark:border-gray-600 p-4 rounded">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300">WACC 配置参数 (可选)</summary>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
           {/* Use InputField helper for WACC params */}
           <InputField
            id="targetDebtRatio"
            label="目标债务比率"
            value={waccParams.targetDebtRatio}
            onChange={handleWaccChange}
            type="number"
            step="0.1"
            unit="%"
            disabled={isLoading}
          />
          <InputField
            id="costOfDebt"
            label="税前债务成本"
            value={waccParams.costOfDebt}
            onChange={handleWaccChange}
            type="number"
            step="0.1"
            unit="%"
            disabled={isLoading}
          />
          <InputField
            id="taxRate"
            label="所得税税率"
            value={waccParams.taxRate}
            onChange={handleWaccChange}
            type="number"
            step="0.1"
            unit="%"
            disabled={isLoading}
          />
           <InputField
            id="riskFreeRate"
            label="无风险利率"
            value={waccParams.riskFreeRate}
            onChange={handleWaccChange}
            type="number"
            step="0.1"
            unit="%"
            disabled={isLoading}
          />
          <InputField
            id="beta"
            label="Beta"
            value={waccParams.beta}
            onChange={handleWaccChange}
            type="number"
            step="0.01"
            disabled={isLoading}
          />
          <InputField
            id="marketRiskPremium"
            label="市场风险溢价"
            value={waccParams.marketRiskPremium}
            onChange={handleWaccChange}
            type="number"
            step="0.01"
            unit="%"
            disabled={isLoading}
          />
          <InputField
            id="sizePremium"
            label="规模溢价"
            value={waccParams.sizePremium}
            onChange={handleWaccChange}
            type="number"
            step="0.01"
            unit="%"
            disabled={isLoading}
          />
        </div>
      </details>


      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !numericCode.trim()} // Disable if numeric code is empty
        className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? '正在计算...' : '获取估值'}
      </button>
    </form>
  );
};

export default ValuationForm;
