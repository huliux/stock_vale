import pytest
from typing import List
from decimal import Decimal

from api.main import generate_axis_values_backend, app # 导入 app 以便 TestClient 使用
from fastapi.testclient import TestClient
from api.models import ValuationInput, SensitivityAnalysisConfig, DcfBasicAssumptions, DcfAdvancedAssumptions, GeneralAssumptions, CompanyInfo, SensitivityAxis, MetricType
from unittest.mock import patch # 用于 mock

# --- 测试 generate_axis_values_backend ---
# (generate_axis_values_backend 函数本身已从 api.main 导入，无需在此处重定义)

client = TestClient(app)

@pytest.mark.parametrize(
    "center, step, points, expected",
    [
        (0.08, 0.005, 5, [pytest.approx(0.07), pytest.approx(0.075), pytest.approx(0.08), pytest.approx(0.085), pytest.approx(0.09)]),
        (8.0, 0.5, 3, [pytest.approx(7.5), pytest.approx(8.0), pytest.approx(8.5)]),
        (0.025, 0.001, 7, [pytest.approx(0.022), pytest.approx(0.023), pytest.approx(0.024), pytest.approx(0.025), pytest.approx(0.026), pytest.approx(0.027), pytest.approx(0.028)]),
        # 测试偶数点数自动变奇数
        (10.0, 1.0, 4, [pytest.approx(8.0), pytest.approx(9.0), pytest.approx(10.0), pytest.approx(11.0), pytest.approx(12.0)]), # 4 -> 5 points
        # 测试点数为1
        (5.0, 0.1, 1, [pytest.approx(5.0)]),
        # 测试点数小于1 (应默认为3)
        (5.0, 0.1, 0, [pytest.approx(4.9), pytest.approx(5.0), pytest.approx(5.1)]),
        # 测试负中心值
        (-0.05, 0.01, 3, [pytest.approx(-0.06), pytest.approx(-0.05), pytest.approx(-0.04)]),
        # 测试负步长 (虽然不常见，但逻辑上应支持)
        (0.1, -0.01, 3, [pytest.approx(0.11), pytest.approx(0.1), pytest.approx(0.09)]),
    ]
)
def test_generate_axis_values_backend(center, step, points, expected):
    """测试后端轴值生成函数的各种情况"""
    result = generate_axis_values_backend(center, step, points)
    assert result == expected
    # 检查点数是否符合预期（考虑了偶数+1和小于1变3）
    expected_points = max(3, points) if points < 1 else (points if points % 2 != 0 else points + 1)
    assert len(result) == expected_points

# TODO: 添加更多测试用例，例如：
# - 测试 API 端点处理 WACC 轴重新生成的逻辑 (需要 Mocking)
# - 测试 API 端点处理非 WACC 轴的行为
# - 测试 API 响应中返回的轴值是否正确
