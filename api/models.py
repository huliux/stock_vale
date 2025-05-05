from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class StockValuationRequest(BaseModel):
    """
    Request model for stock valuation endpoint.
    """
    ts_code: str = Field(..., description="The stock ticker symbol (e.g., '000001.SZ')")
    # market: Optional[str] = Field(default="A", description="Market identifier (e.g., 'A', 'HK')") # Future use

class StockValuationResponse(BaseModel):
    """
    Response model for stock valuation endpoint.
    """
    stock_info: Dict[str, Any] = Field(..., description="Basic information about the stock")
    valuation_results: Dict[str, Any] = Field(..., description="Calculated valuation metrics and recommendation")
    # error: Optional[str] = Field(default=None, description="Error message if calculation failed") # Future use
