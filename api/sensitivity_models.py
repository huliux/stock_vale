from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any

class SensitivityAxis(BaseModel):
    """定义敏感性分析的一个轴"""
    parameter_name: str = Field(..., description="要变化的参数名 (例如 'wacc', 'exit_multiple', 'perpetual_growth_rate')")
    values: List[float] = Field(..., description="该参数要测试的值列表")

from typing import List, Optional, Union, Dict, Any, Literal

# --- Sensitivity Analysis Models ---

SUPPORTED_SENSITIVITY_OUTPUT_METRICS = Literal[
    "value_per_share", 
    "enterprise_value", 
    "equity_value", 
    "ev_ebitda", # 注意: EBITDA 可能需要确认是末期预测值还是 LTM
    "tv_ev_ratio" # 终值占企业价值比例
]

class SensitivityAxis(BaseModel):
    """定义敏感性分析的一个轴"""
    parameter_name: str = Field(..., description="要变化的参数名 (例如 'wacc', 'exit_multiple', 'perpetual_growth_rate')")
    values: List[float] = Field(..., description="该参数要测试的值列表")

class SensitivityAnalysisRequest(BaseModel):
    """敏感性分析的请求配置"""
    row_axis: SensitivityAxis = Field(..., description="定义行轴的参数和值")
    column_axis: SensitivityAxis = Field(..., description="定义列轴的参数和值")
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
