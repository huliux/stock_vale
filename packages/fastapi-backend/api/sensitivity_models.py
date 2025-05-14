from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from enum import Enum # Import Enum

from typing import List, Optional, Union, Dict, Any, Literal

# --- MetricType Enum ---
class MetricType(Enum):
    # Input Parameters for Sensitivity Axes
    WACC = "wacc"
    TERMINAL_GROWTH_RATE = "perpetual_growth_rate"
    TERMINAL_EBITDA_MULTIPLE = "exit_multiple" # Renamed from EXIT_MULTIPLE, value is "exit_multiple"

    # Output Metrics (keys for result_tables and for identifying parameters in DcfForecastDetails)
    VALUE_PER_SHARE = "value_per_share" # Matches DcfForecastDetails.value_per_share
    ENTERPRISE_VALUE = "enterprise_value"
    EQUITY_VALUE = "equity_value"
    EV_EBITDA = "ev_ebitda" # Key used in result_tables
    DCF_IMPLIED_PE = "dcf_implied_pe" # Key used in result_tables
    TV_EV_RATIO = "tv_ev_ratio"

    # Values from DcfForecastDetails that might be used as base for axis generation
    WACC_USED = "wacc_used"
    PERPETUAL_GROWTH_RATE_USED = "perpetual_growth_rate_used"
    EXIT_MULTIPLE_USED = "exit_multiple_used" # This is the actual value from DcfForecastDetails
    EV_EBITDA_TERMINAL = "ev_ebitda_terminal" # This is also from DcfForecastDetails, often used as base for exit_multiple axis


# --- Sensitivity Analysis Models ---

SUPPORTED_SENSITIVITY_OUTPUT_METRICS = Literal[
    "value_per_share",
    "enterprise_value",
    "equity_value",
    "ev_ebitda", # 注意: EBITDA 可能需要确认是末期预测值还是 LTM
    "dcf_implied_pe", # 添加 DCF Implied PE
    "tv_ev_ratio" # 终值占企业价值比例
]

class SensitivityAxisInput(BaseModel): # 重命名以区分，并对应计划
    """定义敏感性分析的一个轴的输入配置"""
    parameter_name: str = Field(..., description="要变化的参数名 (例如 'wacc', 'exit_multiple', 'perpetual_growth_rate')")
    values: List[float] = Field(..., description="该参数要测试的值列表 (对于非WACC轴，或WACC轴的初始列表)")
    step: Optional[float] = Field(None, description="该轴的步长 (主要用于WACC轴的后端重新生成)")
    points: Optional[int] = Field(None, description="该轴的点数 (主要用于WACC轴的后端重新生成)")

class SensitivityAnalysisRequest(BaseModel):
    """敏感性分析的请求配置"""
    row_axis: SensitivityAxisInput = Field(..., description="定义行轴的参数和值")
    column_axis: SensitivityAxisInput = Field(..., description="定义列轴的参数和值")
    # output_metric 字段移除，后端将计算所有支持的指标

class SensitivityAnalysisResult(BaseModel):
    """敏感性分析的结果"""
    row_parameter: str = Field(..., description="行轴使用的参数名")
    column_parameter: str = Field(..., description="列轴使用的参数名")
    row_values: List[float] = Field(..., description="行轴使用的值列表")
    column_values: List[float] = Field(..., description="列轴使用的值列表")
    # 使用字典存储多个指标的结果表
    result_tables: Dict[str, List[List[Optional[float]]]] = Field(
        ..., 
        description="包含多个输出指标及其对应二维结果表格的字典，键为指标名 (如 'value_per_share')"
    )
