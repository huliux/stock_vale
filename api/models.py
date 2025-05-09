from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal # Ensure Decimal is imported
from .sensitivity_models import SensitivityAnalysisRequest, SensitivityAnalysisResult # Import new models

# --- Request Model ---

class StockValuationRequest(BaseModel):
    """
    Request model for stock valuation endpoint (Revised for Streamlit & LLM).
    """
    ts_code: str = Field(..., description="股票代码 (例如 '600519.SH')")
    market: Optional[str] = Field(default="A", description="市场标识 ('A', 'HK', etc.) - 用于数据获取")
    valuation_date: Optional[str] = Field(None, description="估值基准日期 (YYYY-MM-DD)，默认为最新可用日期")

    # --- DCF 核心假设 ---
    forecast_years: int = Field(default=5, ge=1, le=20, description="预测期年数")
    # 收入预测
    cagr_decay_rate: Optional[float] = Field(None, ge=0, le=1, description="历史 CAGR 年衰减率 (0到1之间)，留空则使用默认值")
    # 利润率预测
    op_margin_forecast_mode: str = Field(default='historical_median', description="营业利润率预测模式 ('historical_median' 或 'transition_to_target')")
    target_operating_margin: Optional[float] = Field(None, description="目标营业利润率 (仅在 transition_to_target 模式下有效)")
    op_margin_transition_years: Optional[int] = Field(None, ge=1, description="营业利润率过渡年数 (仅在 transition_to_target 模式下有效)")
    # SGA & RD 预测
    sga_rd_ratio_forecast_mode: str = Field(default='historical_median', description="SGA&RD 占收入比预测模式")
    target_sga_rd_to_revenue_ratio: Optional[float] = Field(None, description="目标 SGA&RD 占收入比")
    sga_rd_transition_years: Optional[int] = Field(None, ge=1, description="SGA&RD 比率过渡年数")
    # D&A 预测
    da_ratio_forecast_mode: str = Field(default='historical_median', description="D&A 占收入比预测模式")
    target_da_to_revenue_ratio: Optional[float] = Field(None, description="目标 D&A 占收入比")
    da_ratio_transition_years: Optional[int] = Field(None, ge=1, description="D&A 比率过渡年数")
    # Capex 预测
    capex_ratio_forecast_mode: str = Field(default='historical_median', description="Capex 占收入比预测模式")
    target_capex_to_revenue_ratio: Optional[float] = Field(None, description="目标 Capex 占收入比")
    capex_ratio_transition_years: Optional[int] = Field(None, ge=1, description="Capex 比率过渡年数")
    # NWC 周转天数预测
    nwc_days_forecast_mode: str = Field(default='historical_median', description="核心 NWC 周转天数预测模式")
    target_accounts_receivable_days: Optional[float] = Field(None, ge=0, description="目标应收账款周转天数 (DSO)")
    target_inventory_days: Optional[float] = Field(None, ge=0, description="目标存货周转天数 (DIO)")
    target_accounts_payable_days: Optional[float] = Field(None, ge=0, description="目标应付账款周转天数 (DPO)")
    nwc_days_transition_years: Optional[int] = Field(None, ge=1, description="NWC 周转天数过渡年数")
    # 其他 NWC 比率预测
    other_nwc_ratio_forecast_mode: str = Field(default='historical_median', description="其他 NWC 项目占收入比预测模式")
    target_other_current_assets_to_revenue_ratio: Optional[float] = Field(None, description="目标其他流动资产占收入比")
    target_other_current_liabilities_to_revenue_ratio: Optional[float] = Field(None, description="目标其他流动负债占收入比")
    other_nwc_ratio_transition_years: Optional[int] = Field(None, ge=1, description="其他 NWC 比率过渡年数")
    # 税率
    target_effective_tax_rate: Optional[float] = Field(None, ge=0, le=1, description="目标有效所得税率，留空则使用默认值")

    # --- WACC 计算参数 (保留，允许用户覆盖默认值) ---
    wacc_weight_mode: Optional[str] = Field("target", description="WACC权重计算模式: 'target' (使用目标债务比例) 或 'market' (使用最新市场价值计算权重)", pattern="^(target|market)$")
    target_debt_ratio: Optional[float] = Field(None, ge=0, le=1, description="目标资本结构中的债务比例 D/(D+E) (仅在 wacc_weight_mode='target' 时有效)")
    cost_of_debt: Optional[float] = Field(None, ge=0, description="税前债务成本 (Rd)")
    risk_free_rate: Optional[float] = Field(None, ge=0, description="无风险利率 (Rf)")
    beta: Optional[float] = Field(None, description="贝塔系数 (Levered Beta)")
    market_risk_premium: Optional[float] = Field(None, ge=0, description="市场风险溢价 (MRP)")
    size_premium: Optional[float] = Field(None, description="规模溢价 (可选)")

    # --- 终值计算参数 ---
    terminal_value_method: str = Field(default='exit_multiple', description="终值计算方法 ('exit_multiple' 或 'perpetual_growth')")
    exit_multiple: Optional[float] = Field(None, ge=0, description="退出乘数 (基于 EBITDA，仅在 exit_multiple 模式下有效)")
    perpetual_growth_rate: Optional[float] = Field(None, description="永续增长率 (仅在 perpetual_growth 模式下有效)")

    # --- Sensitivity Analysis ---
    sensitivity_analysis: Optional[SensitivityAnalysisRequest] = Field(None, description="敏感性分析配置 (可选)")

    # --- LLM Control ---
    request_llm_summary: Optional[bool] = Field(True, description="是否请求 LLM 分析总结")


# --- Response Models ---

class StockBasicInfoModel(BaseModel):
    """股票基本信息模型"""
    ts_code: Optional[str] = None
    name: Optional[str] = None
    industry: Optional[str] = None
    list_date: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    latest_pe_ttm: Optional[float] = None
    latest_pb_mrq: Optional[float] = None
    total_shares: Optional[float] = None # Store as float for JSON consistency
    free_float_shares: Optional[float] = None # Store as float for JSON consistency
    ttm_dps: Optional[Decimal] = Field(None, description="过去十二个月每股股息 (TTM DPS)")
    dividend_yield: Optional[Decimal] = Field(None, description="股息率 (基于TTM DPS和最新股价)")
    # Add any other fields that might be in the basic_info dict passed from DataProcessor
    # For Pydantic V2, to handle extra fields in input dict if they are not strictly matching
    model_config = ConfigDict(extra="ignore")


class DividendAnalysis(BaseModel):
    """股息分析详情。"""
    current_yield_pct: Optional[float] = Field(None, description="最新股息率 (%)")
    avg_dividend_3y: Optional[float] = Field(None, description="近三年平均每股股息")
    payout_ratio_pct: Optional[float] = Field(None, description="最新股息支付率 (%)")

class GrowthAnalysis(BaseModel):
    """增长分析详情。"""
    net_income_cagr_3y: Optional[float] = Field(None, description="近三年净利润复合年增长率 (%)")
    revenue_cagr_3y: Optional[float] = Field(None, description="近三年收入复合年增长率 (%)")

class OtherAnalysis(BaseModel):
    """其他分析容器。"""
    dividend_analysis: Optional[DividendAnalysis] = None
    growth_analysis: Optional[GrowthAnalysis] = None

class DcfForecastDetails(BaseModel):
    """存储核心 DCF 计算结果的详细信息。"""
    enterprise_value: Optional[float] = Field(None, description="企业价值 (EV)")
    equity_value: Optional[float] = Field(None, description="股权价值")
    value_per_share: Optional[float] = Field(None, description="每股价值")
    net_debt: Optional[float] = Field(None, description="计算使用的净债务")
    pv_forecast_ufcf: Optional[float] = Field(None, description="预测期 UFCF 现值合计")
    pv_terminal_value: Optional[float] = Field(None, description="终值现值")
    terminal_value: Optional[float] = Field(None, description="终值")
    wacc_used: Optional[float] = Field(None, description="计算使用的 WACC")
    cost_of_equity_used: Optional[float] = Field(None, description="计算使用的股权成本 (Ke)")
    terminal_value_method_used: Optional[str] = Field(None, description="终值计算方法")
    exit_multiple_used: Optional[float] = Field(None, description="使用的退出乘数")
    perpetual_growth_rate_used: Optional[float] = Field(None, description="使用的永续增长率")
    forecast_period_years: Optional[int] = Field(None, description="预测期年数")
    dcf_implied_diluted_pe: Optional[float] = Field(None, description="DCF估值对应的稀释市盈率(基于最近年报EPS)")

class ValuationResultsContainer(BaseModel):
    """(修订版) 包含所有计算结果的容器。"""
    latest_price: Optional[float] = Field(None, description="用于计算的最新股价")
    current_pe: Optional[float] = Field(None, description="当前市盈率 (PE)")
    current_pb: Optional[float] = Field(None, description="当前市净率 (PB)")
    dcf_forecast_details: Optional[DcfForecastDetails] = Field(None, description="基于预测的核心 DCF 估值详情")
    other_analysis: Optional[OtherAnalysis] = Field(None, description="股息和增长分析")
    llm_analysis_summary: Optional[str] = Field(None, description="LLM 生成的投资分析摘要 (Markdown 格式)")
    data_warnings: Optional[List[str]] = Field(None, description="数据处理过程中产生的警告信息列表")
    detailed_forecast_table: Optional[List[Dict[str, Any]]] = Field(None, description="详细的逐年财务预测表格")
    sensitivity_analysis_result: Optional[SensitivityAnalysisResult] = Field(None, description="敏感性分析结果 (可选)")

class StockValuationResponse(BaseModel):
    """
    (修订版) 股票估值端点的响应模型。
    """
    stock_info: StockBasicInfoModel = Field(..., description="股票基本信息") # Changed to StockBasicInfoModel
    valuation_results: ValuationResultsContainer = Field(..., description="包含所有计算结果的容器")
    error: Optional[str] = Field(default=None, description="高级别错误信息 (例如，无法获取数据)")
