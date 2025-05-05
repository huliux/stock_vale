from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
from .models import StockValuationRequest, StockValuationResponse # Use relative import
from data_fetcher import AshareDataFetcher # Assuming data_fetcher.py is in the root
# Defer ValuationCalculator import to endpoint
# from valuation_calculator import ValuationCalculator
import pandas as pd

app = FastAPI(
    title="Stock Valuation API",
    description="API for fetching stock data and calculating valuations.",
    version="0.1.0",
)

# --- CORS Configuration ---
# WARNING: Allowing all origins is suitable for development but insecure for production.
# Restrict origins in a production environment.
origins = [
    "http://localhost", # Allow requests from localhost (any port)
    "http://localhost:3000", # Explicitly allow default Next.js dev port
    # Add other origins as needed, e.g., deployed frontend URL
    "*" # Allow all origins (use with caution)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)
# --- End CORS Configuration ---

@app.get("/")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Stock Valuation API"}

@app.post("/api/v1/valuation", response_model=StockValuationResponse)
async def calculate_valuation_endpoint(request: StockValuationRequest):
    """
    Calculates valuation metrics for a given stock code.
    """
    try:
        # 1. Instantiate Data Fetcher (Assuming A-share for now)
        fetcher = AshareDataFetcher(ts_code=request.ts_code)

        # 2. Fetch Data
        stock_info = fetcher.get_stock_info()
        latest_price = fetcher.get_latest_price()
        total_shares = fetcher.get_total_shares() # In 10k shares, need conversion? Check calculator usage
        financials = fetcher.get_financial_data()

        # Check for empty financials *before* proceeding further
        if financials.empty:
            raise HTTPException(status_code=404, detail=f"Financial data not found for {request.ts_code}")

        # Fetch dividends only if financials are available
        dividends = fetcher.get_dividend_data()

        # 3. Calculate Market Cap (Ensure units match calculator expectations)
        # Calculator uses market_cap in billions (亿元) for PE, but EV uses raw value.
        # Let's pass raw value and let calculator handle units if needed, or adjust here.
        # total_shares from DB is in 10k shares. Convert to shares.
        market_cap_raw = latest_price * (total_shares * 10000)
        market_cap_billion = market_cap_raw / 100000000 # Convert to billions (亿元) for PE calc consistency

        # 4. Instantiate Calculator (Import inside endpoint)
        from valuation_calculator import ValuationCalculator
        calculator = ValuationCalculator(
            stock_info=stock_info,
            latest_price=latest_price,
            total_shares=total_shares * 10000, # Pass total shares in actual number
            financials=financials,
            dividends=dividends,
            market_cap=market_cap_billion # Pass market cap in billions
        )

        # 5. Perform Calculations (Example subset)
        pe_ratio = calculator.calculate_pe_ratio()
        pb_ratio = calculator.calculate_pb_ratio()
        current_yield, div_history, avg_div, payout_ratio = calculator.calculate_dividend_yield()
        # Use default rates for DDM for now
        ddm_results, ddm_error = calculator.calculate_ddm_valuation([], [])

        # 6. Structure Response
        valuation_results = {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dividend_yield_current": current_yield,
            "dividend_payout_ratio": payout_ratio,
            "ddm_valuation": ddm_results if not ddm_error else {"error": ddm_error},
            # Add more results as needed
        }

        return StockValuationResponse(
            stock_info=stock_info,
            valuation_results=valuation_results
        )

    except ValueError as ve:
        # Handle specific errors like missing price
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Generic error handler
        # Log the error in a real application: logger.error(f"Error calculating valuation for {request.ts_code}: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # This is for local development testing only.
    # Use `uvicorn api.main:app --reload` in the terminal for development.
    uvicorn.run(app, host="0.0.0.0", port=8124)
