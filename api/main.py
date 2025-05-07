from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
# Import all models needed
from .models import (
    StockValuationRequest, StockValuationResponse, ValuationResultsContainer,
    ValuationMethodResult, OtherAnalysis, DividendAnalysis, GrowthAnalysis,
    InvestmentAdvice
)
from data_fetcher import AshareDataFetcher # Assuming data_fetcher.py is in the root
# Defer ValuationCalculator import to endpoint
# from valuation_calculator import ValuationCalculator
import pandas as pd
import traceback # For detailed error logging

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

@app.post("/api/v1/valuation", response_model=StockValuationResponse, summary="Calculate Stock Valuation")
async def calculate_valuation_endpoint(request: StockValuationRequest):
    """
    Calculates comprehensive valuation metrics for a given stock code (ts_code).

    Accepts optional parameters for sensitivity analysis:
    - **pe_multiples**: List of PE ratios (e.g., [15, 20, 25])
    - **pb_multiples**: List of PB ratios (e.g., [1.5, 2.0, 2.5])
    - **ev_ebitda_multiples**: List of EV/EBITDA ratios (e.g., [8, 10, 12])
    - **growth_rates**: List of growth rates [low, mid, high] (e.g., [0.05, 0.08, 0.10]). If None, calculator uses historical data.

    Returns a detailed valuation report including various models, analysis, and investment advice.
    """
    try:
        # 1. Instantiate Data Fetcher
        fetcher = AshareDataFetcher(ts_code=request.ts_code)

        # 2. Fetch Essential Data
        stock_info = fetcher.get_stock_info()
        if not stock_info:
             raise HTTPException(status_code=404, detail=f"Stock info not found for {request.ts_code}")

        latest_price = fetcher.get_latest_price()
        if latest_price is None or latest_price <= 0:
             raise HTTPException(status_code=404, detail=f"Valid latest price not found for {request.ts_code}")

        total_shares = fetcher.get_total_shares() # In 10k shares
        if total_shares is None or total_shares <= 0:
             raise HTTPException(status_code=404, detail=f"Valid total shares not found for {request.ts_code}")

        financials = fetcher.get_financial_data()
        if financials.empty:
            raise HTTPException(status_code=404, detail=f"Financial data not found for {request.ts_code}")

        dividends = fetcher.get_dividend_data() # Can be empty, calculator handles it

        # 3. Calculate Market Cap (in billions - 亿元)
        # total_shares from fetcher is already the actual share count
        market_cap_raw = latest_price * total_shares
        market_cap_billion = market_cap_raw / 100000000

        # 4. Instantiate Calculator (Import inside endpoint to avoid potential circular deps)
        from valuation_calculator import ValuationCalculator
        calculator = ValuationCalculator(
            stock_info=stock_info,
            latest_price=latest_price,
            total_shares=total_shares, # Pass the actual total shares fetched
            financials=financials,
            dividends=dividends,
            market_cap=market_cap_billion # Pass market cap in billions
            # dcf_growth_cap is no longer passed here, calculator reads from env
        )

        # 5. Perform All Calculations
        results_container = ValuationResultsContainer() # Initialize the container

        # Current Metrics
        # Current Metrics & Context
        results_container.latest_price = latest_price # Add the latest price used
        results_container.current_pe = calculator.calculate_pe_ratio()
        results_container.current_pb = calculator.calculate_pb_ratio()
        _, _, results_container.current_ev_ebitda = calculator.calculate_ev()
        # WACC and Ke are now calculated dynamically, remove direct access here

        # Prepare WACC parameters dictionary from request (pass None values if not provided)
        wacc_params = {
            'target_debt_ratio': request.target_debt_ratio,
            'cost_of_debt': request.cost_of_debt,
            'tax_rate': request.tax_rate,
            'risk_free_rate': request.risk_free_rate,
            'beta': request.beta,
            'market_risk_premium': request.market_risk_premium,
            'size_premium': request.size_premium
        }
        # Filter out None values if calculator expects only provided overrides
        wacc_params = {k: v for k, v in wacc_params.items() if v is not None}


        # Absolute Valuation Models (Pass wacc_params)
        # Note: We are passing None for discount_rates_override, letting the calculator derive them
        dcf_fcff_basic_res, dcf_fcff_basic_err = calculator.perform_fcff_valuation_basic_capex(request.growth_rates, None, wacc_params)
        results_container.dcf_fcff_basic_capex = ValuationMethodResult(results=dcf_fcff_basic_res, error_message=dcf_fcff_basic_err)

        dcf_fcfe_basic_res, dcf_fcfe_basic_err = calculator.perform_fcfe_valuation_basic_capex(request.growth_rates, None, wacc_params)
        results_container.dcf_fcfe_basic_capex = ValuationMethodResult(results=dcf_fcfe_basic_res, error_message=dcf_fcfe_basic_err)

        dcf_fcff_full_res, dcf_fcff_full_err = calculator.perform_fcff_valuation_full_capex(request.growth_rates, None, wacc_params)
        results_container.dcf_fcff_full_capex = ValuationMethodResult(results=dcf_fcff_full_res, error_message=dcf_fcff_full_err)

        dcf_fcfe_full_res, dcf_fcfe_full_err = calculator.perform_fcfe_valuation_full_capex(request.growth_rates, None, wacc_params)
        results_container.dcf_fcfe_full_capex = ValuationMethodResult(results=dcf_fcfe_full_res, error_message=dcf_fcfe_full_err)

        ddm_res, ddm_err = calculator.calculate_ddm_valuation(request.growth_rates, None, wacc_params)
        results_container.ddm = ValuationMethodResult(results=ddm_res, error_message=ddm_err)

        # Retrieve calculated WACC and Ke after calculations that trigger them
        results_container.calculated_wacc_pct = calculator.last_calculated_wacc * 100 if hasattr(calculator, 'last_calculated_wacc') and calculator.last_calculated_wacc is not None else None
        results_container.calculated_cost_of_equity_pct = calculator.last_calculated_ke * 100 if hasattr(calculator, 'last_calculated_ke') and calculator.last_calculated_ke is not None else None


        # Other Analysis
        other_analysis_data = calculator.get_other_analysis()
        if other_analysis_data:
            results_container.other_analysis = OtherAnalysis(
                dividend_analysis=DividendAnalysis(**other_analysis_data.get('dividend_analysis', {})),
                growth_analysis=GrowthAnalysis(**other_analysis_data.get('growth_analysis', {}))
            )

        # Combo Valuations & Investment Advice
        # TODO: Pass the actual main_dcf_result_dict when forecast DCF is implemented
        combo_vals, advice_data = calculator.get_combo_valuations(
            main_dcf_result_dict=None, # Placeholder for forecast DCF result
            pe_multiples=request.pe_multiples,
            pb_multiples=request.pb_multiples,
            ev_ebitda_multiples=request.ev_ebitda_multiples,
            # Removed growth_rates=request.growth_rates, as it's not an expected argument
            # Pass the wacc_params dictionary here
            wacc_params=wacc_params
        )
        results_container.combo_valuations = combo_vals
        if advice_data:
            results_container.investment_advice = InvestmentAdvice(**advice_data)


        # 6. Structure Final Response
        return StockValuationResponse(
            stock_info=stock_info,
            valuation_results=results_container
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except ValueError as ve:
        # Handle specific data fetching/validation errors
        print(f"ValueError during valuation for {request.ts_code}: {ve}\n{traceback.format_exc()}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Generic error handler for unexpected issues
        print(f"Unexpected error calculating valuation for {request.ts_code}: {e}\n{traceback.format_exc()}")
        # Log the error in a real application: logger.error(...)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred. Please try again later.")

if __name__ == "__main__":
    import uvicorn
    # This is for local development testing only.
    # Use `uvicorn api.main:app --reload` in the terminal for development.
    uvicorn.run(app, host="0.0.0.0", port=8124)
