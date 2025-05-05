// Define types based on the backend API response structure (api/models.py)

export interface StockInfo {
  ts_code: string;
  name: string;
  industry: string;
  // Add other fields from backend's get_stock_info if needed
  [key: string]: any; // Allow other potential fields
}

export interface ValuationResults {
  pe_ratio: number | null;
  pb_ratio: number | null;
  dividend_yield_current: number;
  dividend_payout_ratio: number;
  ddm_valuation: {
      growth_rate?: number;
      discount_rate?: number;
      value?: number;
      premium?: number;
      error?: string; // Include potential error field
  }[] | { error?: string }; // Can be an array or an error object
  // Add other valuation metrics returned by the backend
  [key: string]: any; // Allow other potential fields
}

export interface StockValuationResponse {
  stock_info: StockInfo;
  valuation_results: ValuationResults;
  // error?: string; // Optional top-level error field if added later
}
