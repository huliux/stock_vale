"use client"; // Required for useState

import { useState } from "react";
import ValuationForm from "@/components/features/valuation/ValuationForm"; // Import actual component
import ResultsDisplay from "@/components/features/valuation/ResultsDisplay"; // Import actual component
import { StockValuationResponse } from "@/types/api";

// Define FormData interface here as well, or import if moved to types
interface FormData {
  tsCode: string;
  targetDebtRatio: string;
  costOfDebt: string;
  taxRate: string;
  riskFreeRate: string;
  beta: string;
  marketRiskPremium: string;
  sizePremium: string;
}

export default function Home() {
  const [results, setResults] = useState<StockValuationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to safely parse float and convert percentage string to decimal
  const parsePercentToDecimal = (value: string | undefined | null): number | null => {
    if (value === undefined || value === null || value.trim() === '') {
      return null; // Treat empty string as null (don't send to backend)
    }
    const num = parseFloat(value);
    return isNaN(num) ? null : num / 100.0; // Convert percentage to decimal
  };

  // Helper function to safely parse float string
  const parseFloatInput = (value: string | undefined | null): number | null => {
     if (value === undefined || value === null || value.trim() === '') {
      return null; // Treat empty string as null
    }
    const num = parseFloat(value);
    return isNaN(num) ? null : num;
  };


  // Update the handler function signature and logic
  const handleValuationRequest = async (formData: FormData) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // Construct the request body, converting percentages to decimals
      // Only include parameters if they have valid numeric values
      const requestBody: { [key: string]: any } = {
        ts_code: formData.tsCode.trim(),
      };

      const waccParams = {
        target_debt_ratio: parsePercentToDecimal(formData.targetDebtRatio),
        cost_of_debt: parsePercentToDecimal(formData.costOfDebt),
        tax_rate: parsePercentToDecimal(formData.taxRate),
        risk_free_rate: parsePercentToDecimal(formData.riskFreeRate),
        beta: parseFloatInput(formData.beta),
        market_risk_premium: parsePercentToDecimal(formData.marketRiskPremium),
        size_premium: parsePercentToDecimal(formData.sizePremium),
      };

      // Add WACC params to request body only if they are not null
      for (const [key, value] of Object.entries(waccParams)) {
        if (value !== null) {
          requestBody[key] = value;
        }
      }

      // IMPORTANT: Replace with your actual API endpoint URL
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8124";
      const response = await fetch(`${apiUrl}/api/v1/valuation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: StockValuationResponse = await response.json();
      setResults(data);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 sm:p-12 md:p-24 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-4xl">
        <h1 className="text-3xl sm:text-4xl font-bold text-center mb-8 sm:mb-12">
          股票估值神器
        </h1>

        {/* Integrate ValuationForm - onSubmit now expects FormData */}
        {/* The form component itself is already updated */}
        <ValuationForm onSubmit={handleValuationRequest} isLoading={isLoading} />


        {isLoading && (
          <div className="text-center text-blue-600 dark:text-blue-400 mt-8"> {/* Added margin top */}
            正在加载结果...
          </div>
        )}

        {error && (
          <div className="text-center text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-4 rounded-md mt-8"> {/* Added margin top */}
            错误: {error}
          </div>
        )}

        {results && !error && (
           // Integrate ResultsDisplay - No changes needed here as it accepts StockValuationResponse
           <ResultsDisplay results={results} />
        )}
      </div>
    </main>
  );
}
