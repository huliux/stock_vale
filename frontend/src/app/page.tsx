"use client"; // Required for useState

import { useState } from "react";
import ValuationForm from "@/components/features/valuation/ValuationForm"; // Import actual component
import ResultsDisplay from "@/components/features/valuation/ResultsDisplay"; // Import actual component
import { StockValuationResponse } from "@/types/api";

export default function Home() {
  const [results, setResults] = useState<StockValuationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleValuationRequest = async (tsCode: string) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // IMPORTANT: Replace with your actual API endpoint URL
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8124";
      const response = await fetch(`${apiUrl}/api/v1/valuation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ts_code: tsCode }),
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

        {/* Integrate ValuationForm */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-8">
           <ValuationForm onSubmit={handleValuationRequest} isLoading={isLoading} />
        </div>

        {isLoading && (
          <div className="text-center text-blue-600 dark:text-blue-400">
            正在加载结果...
          </div>
        )}

        {error && (
          <div className="text-center text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-4 rounded-md">
            错误: {error}
          </div>
        )}

        {results && !error && (
           // Integrate ResultsDisplay
           <ResultsDisplay results={results} />
        )}
      </div>
    </main>
  );
}
