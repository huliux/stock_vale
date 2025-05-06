from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union

# --- Request Model ---

class StockValuationRequest(BaseModel):
    """
    Request model for stock valuation endpoint.
    """
    ts_code: str = Field(..., description="The stock ticker symbol (e.g., '600519.SH')")
    # --- Optional parameters for valuation sensitivity ---
    pe_multiples: Optional[List[float]] = Field(
        default=[15, 20, 25],
        description="PE multiples for relative valuation sensitivity analysis."
    )
    pb_multiples: Optional[List[float]] = Field(
        default=[1.5, 2.0, 2.5],
        description="PB multiples for relative valuation sensitivity analysis."
    )
    ev_ebitda_multiples: Optional[List[float]] = Field(
        default=[8, 10, 12],
        description="EV/EBITDA multiples for relative valuation sensitivity analysis (used in combo)."
    )
    # dcf_growth_cap removed, will be configured via .env
    growth_rates: Optional[List[float]] = Field(
        default=None, # Let calculator determine defaults based on history if None
        description="Growth rates [low, mid, high] for DCF/DDM sensitivity. Overrides historical calculation if provided."
    )
    # discount_rates: Optional[List[float]] = Field(
    #     default=None, # Let calculator determine defaults based on WACC/Ke if None
    #     description="Discount rates [low, mid, high] for DCF/DDM sensitivity. Overrides WACC/Ke calculation if provided."
    # ) # Let's rely on WACC/Ke based rates for now

    # --- Optional parameters for WACC calculation ---
    target_debt_ratio: Optional[float] = Field(None, ge=0, le=1, description="Target Debt / Total Capital ratio for WACC calculation (e.g., 0.45 for 45%). Overrides calculation based on market values if provided.")
    cost_of_debt: Optional[float] = Field(None, ge=0, description="Pre-tax Cost of Debt for WACC calculation (e.g., 0.05 for 5%). Overrides default if provided.")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Effective Tax Rate for WACC calculation (e.g., 0.25 for 25%). Overrides default if provided.")
    risk_free_rate: Optional[float] = Field(None, ge=0, description="Risk-Free Rate for Cost of Equity (Ke) calculation (e.g., 0.03 for 3%). Overrides default if provided.")
    beta: Optional[float] = Field(None, description="Levered Beta for Cost of Equity (Ke) calculation. Overrides default if provided.")
    market_risk_premium: Optional[float] = Field(None, ge=0, description="Market Risk Premium for Cost of Equity (Ke) calculation (e.g., 0.0611 for 6.11%). Overrides default if provided.")
    size_premium: Optional[float] = Field(None, description="Size Premium for Cost of Equity (Ke) calculation (e.g., 0.0 for 0%). Overrides default if provided.")


# --- Response Models ---

class ValuationResultItem(BaseModel):
    """Represents a single valuation result from sensitivity analysis."""
    growth_rate: Optional[float] = Field(None, description="Assumed growth rate for this valuation point.")
    discount_rate: Optional[float] = Field(None, description="Assumed discount rate for this valuation point.")
    value: Optional[float] = Field(None, description="Calculated value per share.")
    premium: Optional[float] = Field(None, description="Premium/discount percentage compared to the latest price.")

class ValuationMethodResult(BaseModel):
    """Holds results for a specific valuation method (e.g., DCF, DDM)."""
    results: Optional[List[ValuationResultItem]] = Field(None, description="List of valuation results from sensitivity analysis.")
    error_message: Optional[str] = Field(None, description="Error message if this valuation method failed.")
    # Optional summary fields can be added later if needed (min, max, avg)

class DividendAnalysis(BaseModel):
    """Details of dividend analysis."""
    current_yield_pct: Optional[float] = Field(None, description="Latest dividend yield percentage.")
    avg_dividend_3y: Optional[float] = Field(None, description="Average dividend per share over the last 3 years.")
    payout_ratio_pct: Optional[float] = Field(None, description="Latest dividend payout ratio percentage.")

class GrowthAnalysis(BaseModel):
    """Details of growth analysis."""
    net_income_cagr_3y: Optional[float] = Field(None, description="3-year Compound Annual Growth Rate (CAGR) for net income.")
    revenue_cagr_3y: Optional[float] = Field(None, description="3-year Compound Annual Growth Rate (CAGR) for revenue.")

class OtherAnalysis(BaseModel):
    """Container for other analysis types."""
    dividend_analysis: Optional[DividendAnalysis] = None
    growth_analysis: Optional[GrowthAnalysis] = None

class InvestmentAdvice(BaseModel):
    """Investment advice based on valuation."""
    based_on: Optional[str] = Field(None, description="Valuation methods primarily used for this advice.")
    advice: Optional[str] = Field(None, description="Investment suggestion (e.g., Buy, Sell, Hold).")
    reason: Optional[str] = Field(None, description="Explanation for the advice.")
    min_intrinsic_value: Optional[float] = Field(None, description="Estimated minimum intrinsic value per share.")
    avg_intrinsic_value: Optional[float] = Field(None, description="Estimated average intrinsic value per share.")
    max_intrinsic_value: Optional[float] = Field(None, description="Estimated maximum intrinsic value per share.")
    safety_margin_pct: Optional[float] = Field(None, description="Calculated safety margin percentage based on minimum intrinsic value.")
    reference_info: Optional[str] = Field(None, description="Reference information from other valuation methods.")


class ValuationResultsContainer(BaseModel):
    """Container for all calculated valuation results."""
    # Current Metrics & Context
    latest_price: Optional[float] = Field(None, description="The latest stock price used for these calculations.")
    current_pe: Optional[float] = Field(None, description="Current Price-to-Earnings ratio.")
    current_pb: Optional[float] = Field(None, description="Current Price-to-Book ratio.")
    current_ev_ebitda: Optional[float] = Field(None, description="Current Enterprise Value to EBITDA ratio.")
    calculated_wacc_pct: Optional[float] = Field(None, description="Calculated Weighted Average Cost of Capital (WACC) percentage.")
    calculated_cost_of_equity_pct: Optional[float] = Field(None, description="Calculated Cost of Equity (Ke) percentage.")

    # Absolute Valuation Models
    dcf_fcff_basic_capex: Optional[ValuationMethodResult] = Field(None, description="DCF valuation based on FCFF with basic capex.")
    dcf_fcfe_basic_capex: Optional[ValuationMethodResult] = Field(None, description="DCF valuation based on FCFE with basic capex.")
    dcf_fcff_full_capex: Optional[ValuationMethodResult] = Field(None, description="DCF valuation based on FCFF with full capex.")
    dcf_fcfe_full_capex: Optional[ValuationMethodResult] = Field(None, description="DCF valuation based on FCFE with full capex.")
    ddm: Optional[ValuationMethodResult] = Field(None, description="Dividend Discount Model (DDM) valuation.")

    # Other Analysis
    other_analysis: Optional[OtherAnalysis] = Field(None, description="Dividend and growth analysis.")

    # Combo Valuations - Updated type hint for nested dict and description
    combo_valuations: Optional[Dict[str, Optional[Dict[str, Optional[float]]]]] = Field(None, description="Combined valuation results using descriptive keys (e.g., FCFE_Basic, Avg_FCF_Basic, Composite_Valuation). Each key maps to a dict containing 'value' and 'safety_margin_pct', or null if calculation failed.")

    # Investment Advice
    investment_advice: Optional[InvestmentAdvice] = Field(None, description="Final investment advice based on analysis.")


class StockValuationResponse(BaseModel):
    """
    Response model for stock valuation endpoint.
    """
    stock_info: Dict[str, Any] = Field(..., description="Basic information about the stock.")
    valuation_results: ValuationResultsContainer = Field(..., description="Container for all calculated valuation results.")
    error: Optional[str] = Field(default=None, description="Overall error message if calculation failed at a high level.")
