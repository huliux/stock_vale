import os
import json
import logging
import traceback
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file at the beginning of this module to ensure env vars are available for module-level constants
load_dotenv()

# 假设 DcfForecastDetails 模型定义在 api.models
# 如果不是，需要调整导入路径
try:
    from api.models import DcfForecastDetails
except ImportError:
    # Fallback or define a placeholder if models are not accessible during standalone use
    # This is mainly for type hinting and might not be strictly necessary if only used by main.py
    class DcfForecastDetails: pass

# 假设 decimal_default 辅助函数在 api.utils
try:
    from api.utils import decimal_default
except ImportError:
    # Fallback for decimal_default if utils.py is not found (e.g. standalone testing)
    from decimal import Decimal
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

import requests # For DeepSeek or other HTTP APIs
# Conditional imports for other LLM providers can be inside call_llm_api

logger = logging.getLogger(__name__)

# --- LLM Configuration ---
PROMPT_TEMPLATE_PATH = os.getenv("PROMPT_TEMPLATE_PATH", "config/llm_prompt_template.md")
LLM_API_KEYS = { # API Keys are still loaded from environment
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
    "custom_openai": os.getenv("CUSTOM_LLM_API_KEY"), # For custom OpenAI-compatible models
}

# Default LLM parameters from environment variables
LLM_DEFAULT_TEMPERATURE = float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))
LLM_DEFAULT_TOP_P = float(os.getenv("LLM_DEFAULT_TOP_P", "0.9"))
LLM_DEFAULT_MAX_TOKENS = int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "4000"))
DEEPSEEK_DEFAULT_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
CUSTOM_LLM_DEFAULT_API_BASE_URL = os.getenv("CUSTOM_LLM_API_BASE_URL")
CUSTOM_LLM_DEFAULT_MODEL_ID = os.getenv("CUSTOM_LLM_MODEL_ID")


def load_prompt_template() -> str:
    """从文件加载 Prompt 模板"""
    try:
        with open(PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template file not found at {PROMPT_TEMPLATE_PATH}")
        return "请分析以下数据：\n{data_json}" # Fallback template expects data_json key
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return "请分析以下数据：\n{data_json}"

def format_llm_input_data(
    basic_info: Dict[str, Any],
    dcf_details: Optional[DcfForecastDetails],
    latest_metrics: Dict[str, Any],
    request_assumptions_dict: Dict[str, Any],
    historical_ratios_from_dp: Dict[str, Any],
    other_analysis=None # Placeholder for potential future use
) -> str:
    """将数据格式化为 JSON 字符串以供 Prompt 使用，包含关键假设。"""

    key_assumptions = {
        "forecast_years": request_assumptions_dict.get('forecast_years'),
        "wacc_parameters": {
            "wacc_weight_mode": request_assumptions_dict.get('wacc_weight_mode'),
            "target_debt_ratio_pct": request_assumptions_dict.get('target_debt_ratio') * 100 if request_assumptions_dict.get('target_debt_ratio') is not None else None,
            "cost_of_debt_pct": request_assumptions_dict.get('cost_of_debt') * 100 if request_assumptions_dict.get('cost_of_debt') is not None else None,
            "risk_free_rate_pct": request_assumptions_dict.get('risk_free_rate') * 100 if request_assumptions_dict.get('risk_free_rate') is not None else None,
            "beta": request_assumptions_dict.get('beta'),
            "market_risk_premium_pct": request_assumptions_dict.get('market_risk_premium') * 100 if request_assumptions_dict.get('market_risk_premium') is not None else None,
            "size_premium_pct": request_assumptions_dict.get('size_premium') * 100 if request_assumptions_dict.get('size_premium') is not None else None,
        },
        "effective_tax_rate_pct": request_assumptions_dict.get('target_effective_tax_rate') * 100 if request_assumptions_dict.get('target_effective_tax_rate') is not None else None,
        "terminal_value_method": request_assumptions_dict.get('terminal_value_method'),
        "exit_multiple": request_assumptions_dict.get('exit_multiple') if request_assumptions_dict.get('terminal_value_method') == 'exit_multiple' else None,
        "perpetual_growth_rate_pct": request_assumptions_dict.get('perpetual_growth_rate') * 100 if request_assumptions_dict.get('terminal_value_method') == 'perpetual_growth' and request_assumptions_dict.get('perpetual_growth_rate') is not None else None,
        "revenue_forecast_logic": "CAGR with decay",
        "revenue_initial_cagr_pct": historical_ratios_from_dp.get('revenue_cagr_3y'),
        "revenue_cagr_decay_rate_pct": request_assumptions_dict.get('cagr_decay_rate') * 100 if request_assumptions_dict.get('cagr_decay_rate') is not None else None,
        "prediction_details": {
            "nwc_days_transition_years": request_assumptions_dict.get('nwc_days_transition_years'),
            "other_nwc_ratio_transition_years": request_assumptions_dict.get('other_nwc_ratio_transition_years'),
            "op_margin_transition_years": request_assumptions_dict.get('op_margin_transition_years'),
            "sga_rd_transition_years": request_assumptions_dict.get('sga_rd_transition_years'),
            "da_ratio_transition_years": request_assumptions_dict.get('da_ratio_transition_years'),
            "capex_ratio_transition_years": request_assumptions_dict.get('capex_ratio_transition_years'),
            "op_margin_forecast_mode": request_assumptions_dict.get('op_margin_forecast_mode'),
            "target_operating_margin_pct": request_assumptions_dict.get('target_operating_margin') * 100 if request_assumptions_dict.get('target_operating_margin') is not None else None,
            "sga_rd_ratio_forecast_mode": request_assumptions_dict.get('sga_rd_ratio_forecast_mode'),
            "target_sga_rd_to_revenue_ratio_pct": request_assumptions_dict.get('target_sga_rd_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_sga_rd_to_revenue_ratio') is not None else None,
            "da_ratio_forecast_mode": request_assumptions_dict.get('da_ratio_forecast_mode'),
            "target_da_to_revenue_ratio_pct": request_assumptions_dict.get('target_da_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_da_to_revenue_ratio') is not None else None,
            "capex_ratio_forecast_mode": request_assumptions_dict.get('capex_ratio_forecast_mode'),
            "target_capex_to_revenue_ratio_pct": request_assumptions_dict.get('target_capex_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_capex_to_revenue_ratio') is not None else None,
            "nwc_days_forecast_mode": request_assumptions_dict.get('nwc_days_forecast_mode'),
            "target_accounts_receivable_days": request_assumptions_dict.get('target_accounts_receivable_days'),
            "target_inventory_days": request_assumptions_dict.get('target_inventory_days'),
            "target_accounts_payable_days": request_assumptions_dict.get('target_accounts_payable_days'),
            "other_nwc_ratio_forecast_mode": request_assumptions_dict.get('other_nwc_ratio_forecast_mode'),
            "target_other_current_assets_to_revenue_ratio_pct": request_assumptions_dict.get('target_other_current_assets_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_other_current_assets_to_revenue_ratio') is not None else None,
            "target_other_current_liabilities_to_revenue_ratio_pct": request_assumptions_dict.get('target_other_current_liabilities_to_revenue_ratio') * 100 if request_assumptions_dict.get('target_other_current_liabilities_to_revenue_ratio') is not None else None,
        }
    }

    def clean_dict(d):
        if not isinstance(d, dict):
            return d
        return {k: clean_dict(v) for k, v in d.items() if v is not None and not (isinstance(v, dict) and not clean_dict(v))}

    cleaned_key_assumptions = clean_dict(key_assumptions)

    # Use model_dump() if DcfForecastDetails is a Pydantic model
    dcf_results_dict = dcf_details.model_dump(exclude_none=True) if dcf_details and hasattr(dcf_details, 'model_dump') else (dcf_details.__dict__ if dcf_details else {})
    dcf_results_dict["key_assumptions"] = cleaned_key_assumptions

    data_dict = {
        "stock_info": basic_info or {},
        "dcf_results": dcf_results_dict,
        "reference_metrics": latest_metrics or {},
    }

    if latest_metrics and 'latest_price' in latest_metrics:
         data_dict["stock_info"]["latest_price"] = latest_metrics['latest_price']

    try:
        json_string = json.dumps(data_dict, indent=2, ensure_ascii=False, default=decimal_default)
        return json_string
    except Exception as e:
        logger.error(f"Error formatting data for LLM prompt: {e}")
        return "{}"

def call_llm_api(
    prompt: str,
    provider: str,
    model_id: Optional[str] = None,
    api_base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Optional[str]:
    """
    调用指定的 LLM API。
    Args:
        prompt (str): 发送给 LLM 的提示。
        provider (str): 要使用的 LLM 提供商 (例如 "deepseek", "custom_openai")。
        model_id (Optional[str]): 要使用的模型ID。
        api_base_url (Optional[str]): 自定义模型的API基础URL。
        temperature (Optional[float]): 生成文本的温度。
        top_p (Optional[float]): Top-P采样。
        max_tokens (Optional[int]): 生成文本的最大token数。
    Returns:
        Optional[str]: LLM 的响应或错误信息。
    """
    # 如果provider是'default'或None，使用环境变量中的默认提供商
    if provider is None or provider.lower() == 'default':
        selected_provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
        logger.info(f"--- Using default LLM provider from .env: {selected_provider} ---")
    else:
        selected_provider = provider.lower()
        logger.info(f"--- Calling LLM ({selected_provider}) ---")

    api_key = LLM_API_KEYS.get(selected_provider)
    if not api_key:
        # For custom_openai, API key might be optional if the custom server doesn't require it,
        # or if it's handled by other means (e.g. direct network access on a trusted server).
        # However, the OpenAI SDK typically expects an api_key, even if it's a dummy one for local servers.
        if selected_provider != "custom_openai" or (selected_provider == "custom_openai" and not CUSTOM_LLM_DEFAULT_API_BASE_URL): # Only error if not custom or custom without base_url
            logger.error(f"API Key for {selected_provider} not found or not configured correctly in .env file.")
            return f"错误：未找到或未正确配置 {selected_provider} 的 API Key。"
        elif selected_provider == "custom_openai" and not api_key:
             logger.info(f"API Key for custom_openai not found in .env, will proceed if API base URL is set (assuming no auth or dummy key needed).")
             api_key = "dummy_key_if_not_needed" # OpenAI SDK might require a non-empty key

    # Resolve parameters, using passed values or falling back to defaults from .env
    current_temperature = temperature if temperature is not None else LLM_DEFAULT_TEMPERATURE
    current_top_p = top_p if top_p is not None else LLM_DEFAULT_TOP_P
    current_max_tokens = max_tokens if max_tokens is not None else LLM_DEFAULT_MAX_TOKENS

    try:
        logger.info(f"Attempting to call {selected_provider} API...")
        if selected_provider == "deepseek":
            current_model_id = model_id or DEEPSEEK_DEFAULT_MODEL_NAME
            url = "https://api.deepseek.com/chat/completions" # Or make this configurable if needed
            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "StockValeApp/1.0",
                "Content-Type": "application/json; charset=utf-8"
            }
            payload_obj = {
                "model": current_model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": current_temperature,
                "top_p": current_top_p,
                "max_tokens": current_max_tokens
            }
            logger.info(f"Calling DeepSeek API at {url} with model {current_model_id}, temp={current_temperature}, top_p={current_top_p}, max_tokens={current_max_tokens}")

            json_payload_utf8 = json.dumps(payload_obj, ensure_ascii=False).encode('utf-8')
            response = requests.post(url, headers=headers, data=json_payload_utf8, timeout=180)
            response.raise_for_status()

            response_data = response.json()
            if response_data and 'choices' in response_data and response_data['choices'] and 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                llm_result = response_data['choices'][0]['message']['content']
                logger.info(f"Successfully received response from {selected_provider}.")
                return llm_result
            else:
                logger.warning(f"DeepSeek API response format unexpected: {response_data}")
                return "DeepSeek API 返回格式错误或无有效内容。"

        elif selected_provider == "custom_openai":
            import openai

            current_model_id = model_id or CUSTOM_LLM_DEFAULT_MODEL_ID
            current_api_base_url = api_base_url or CUSTOM_LLM_DEFAULT_API_BASE_URL

            if not current_api_base_url:
                logger.error("Custom OpenAI provider selected, but API Base URL is not configured (neither passed nor in .env).")
                return "错误：自定义OpenAI模型的API Base URL未配置。"
            if not current_model_id:
                logger.error("Custom OpenAI provider selected, but Model ID is not configured (neither passed nor in .env).")
                return "错误：自定义OpenAI模型的Model ID未配置。"

            logger.info(f"Initializing OpenAI client for custom provider: base_url={current_api_base_url}, model={current_model_id}")

            client = openai.OpenAI(
                api_key=api_key, # This will be CUSTOM_LLM_API_KEY or the dummy key
                base_url=current_api_base_url
            )

            logger.info(f"Calling Custom OpenAI API with model {current_model_id}, temp={current_temperature}, top_p={current_top_p}, max_tokens={current_max_tokens}...")

            response = client.chat.completions.create(
                model=current_model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=current_temperature,
                top_p=current_top_p,
                max_tokens=current_max_tokens
            )

            if response.choices and response.choices[0].message and response.choices[0].message.content:
                llm_result = response.choices[0].message.content
                logger.info(f"Successfully received response from {selected_provider}.")
                return llm_result.strip()
            else:
                logger.warning(f"Custom OpenAI API response format unexpected or empty: {response}")
                return "自定义 OpenAI API 返回格式错误或无有效内容。"
        else:
            return f"错误：不支持的 LLM 提供商 '{selected_provider}'。"

    except ImportError as ie:
        logger.error(f"Missing library for {selected_provider}. Please install it. {ie}")
        return f"错误：缺少用于 {selected_provider} 的库，请安装。"
    except Exception as e:
        logger.error(f"Error calling LLM API ({selected_provider}): {e}\n{traceback.format_exc()}")
        return f"调用 LLM API 时出错: {str(e)}"
