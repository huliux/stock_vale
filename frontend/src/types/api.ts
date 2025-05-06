// Define types based on the backend API response structure (api/models.py)

export interface StockInfo {
  ts_code: string;
  name: string;
  industry: string;
}

// Interface for sensitivity results used in DCF and DDM
export interface SensitivityResult {
  growth_rate?: number | null;
  discount_rate?: number | null;
  value?: number | null;
  premium?: number | null;
}

// Interface for DCF/DDM valuation containers
export interface ValuationContainer {
  results?: SensitivityResult[] | null;
  error_message?: string | null;
}

// Interface for Dividend Analysis
export interface DividendAnalysis {
  current_yield_pct?: number | null;
  avg_dividend_3y?: number | null;
  payout_ratio_pct?: number | null;
}

// Interface for Growth Analysis
export interface GrowthAnalysis {
  net_income_cagr_3y?: number | null;
  revenue_cagr_3y?: number | null;
}

// Interface for Other Analysis Container
export interface OtherAnalysisContainer {
  dividend_analysis?: DividendAnalysis | null;
  growth_analysis?: GrowthAnalysis | null;
}

// Interface for the nested structure within combo_valuations
export interface ComboValuationItem {
  value?: number | null;
  safety_margin_pct?: number | null;
}

// Interface for Investment Advice
export interface InvestmentAdvice {
  based_on?: string | null;
  advice?: string | null;
  reason?: string | null;
  min_intrinsic_value?: number | null;
  avg_intrinsic_value?: number | null;
  max_intrinsic_value?: number | null;
  safety_margin_pct?: number | null; // The specific margin used for advice
  reference_info?: string | null;
}

// Updated interface for the main valuation results container
export interface ValuationResultsContainer {
  current_pe?: number | null;
  current_pb?: number | null;
  current_ev_ebitda?: number | null;
  calculated_wacc_pct?: number | null;
  calculated_cost_of_equity_pct?: number | null;
  dcf_fcff_basic_capex?: ValuationContainer | null;
  dcf_fcfe_basic_capex?: ValuationContainer | null;
  dcf_fcff_full_capex?: ValuationContainer | null;
  dcf_fcfe_full_capex?: ValuationContainer | null;
  ddm?: ValuationContainer | null; // Renamed from ddm_valuation
  other_analysis?: OtherAnalysisContainer | null;
  // Type for combo_valuations: Dictionary where keys are strings,
  // and values are either ComboValuationItem or null.
  combo_valuations?: { [key: string]: ComboValuationItem | null } | null;
  investment_advice?: InvestmentAdvice | null;
}

// Updated main response interface
export interface StockValuationResponse {
  stock_info?: StockInfo | null;
  valuation_results?: ValuationResultsContainer | null;
  error?: string | null; // Top-level error field
}
