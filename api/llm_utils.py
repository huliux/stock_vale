import os
import json
import logging
import traceback
from typing import Dict, Any, Optional

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

# --- LLM Configuration (Copied from main.py) ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
PROMPT_TEMPLATE_PATH = os.getenv("PROMPT_TEMPLATE_PATH", "config/llm_prompt_template.md")
LLM_API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
}

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

def call_llm_api(prompt: str) -> Optional[str]:
    """调用配置的 LLM API"""
    logger.info(f"--- Calling LLM ({LLM_PROVIDER}) ---")

    api_key = LLM_API_KEYS.get(LLM_PROVIDER)
    if not api_key or api_key == "AIzaSy...pEU":
        logger.error(f"API Key for {LLM_PROVIDER} not found or not configured correctly in .env file.")
        return f"错误：未找到或未正确配置 {LLM_PROVIDER} 的 API Key。"

    try:
        logger.info(f"Attempting to call {LLM_PROVIDER} API...")
        if LLM_PROVIDER == "gemini":
            import google.generativeai as genai 
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            generation_config = genai.types.GenerationConfig()
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            # print(f"调用 Gemini API (model: gemini-pro)...") # Removed print
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = f"Gemini API 请求被阻止，原因: {response.prompt_feedback.block_reason}"
                if response.prompt_feedback.block_reason_message:
                    block_reason_message += f" - {response.prompt_feedback.block_reason_message}"
                # print(f"Warning: {block_reason_message}") # Removed print
                logger.warning(block_reason_message)
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    partial_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                    if partial_text:
                        return f"{block_reason_message}\n部分返回内容:\n{partial_text}"
                return block_reason_message

            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                 finish_reason_msg = ""
                 if response.candidates and response.candidates[0].finish_reason:
                     finish_reason_msg = f" (Finish Reason: {response.candidates[0].finish_reason.name})"
                 safety_ratings_msg = ""
                 if response.candidates and response.candidates[0].safety_ratings:
                     problematic_ratings = [f"{rating.category.name}: {rating.probability.name}" for rating in response.candidates[0].safety_ratings if rating.probability.name not in ["NEGLIGIBLE", "LOW"]]
                     if problematic_ratings:
                         safety_ratings_msg = f" (Problematic Safety Ratings: {', '.join(problematic_ratings)})"
                 logger.warning(f"Gemini API did not return valid content. {finish_reason_msg}{safety_ratings_msg}")
                 return f"Gemini API 未返回有效内容。{finish_reason_msg}{safety_ratings_msg}"
            
            llm_result = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            logger.info(f"Successfully received response from {LLM_PROVIDER}.")
            return llm_result
        elif LLM_PROVIDER == "openai":
            # Placeholder for OpenAI
            # print("模拟调用 OpenAI API...") # Removed print
            logger.info("Simulating OpenAI API call...")
            return f"OpenAI 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..."
        elif LLM_PROVIDER == "anthropic":
            # Placeholder for Anthropic
            # print("模拟调用 Anthropic API...") # Removed print
            logger.info("Simulating Anthropic API call...")
            return f"Anthropic 分析结果占位符。\n分析内容应基于提供的详细数据和 Prompt 指令生成..."
        elif LLM_PROVIDER == "deepseek":
             url = "https://api.deepseek.com/chat/completions"
             headers = {
                 "Authorization": f"Bearer {api_key}",
                 "User-Agent": "StockValeApp/1.0"
             }
             payload_obj = {
                 "model": "deepseek-chat",
                 "messages": [{"role": "user", "content": prompt}],
             } 
             logger.info(f"Calling DeepSeek API at {url} with model {payload_obj['model']}...")
             
             json_payload_utf8 = json.dumps(payload_obj, ensure_ascii=False).encode('utf-8')
             headers["Content-Type"] = "application/json; charset=utf-8"

             response = requests.post(url, headers=headers, data=json_payload_utf8, timeout=180)
             response.raise_for_status()
             
             response_data = response.json()
             if response_data and 'choices' in response_data and response_data['choices'] and 'message' in response_data['choices'][0] and 'content' in response_data['choices'][0]['message']:
                 llm_result = response_data['choices'][0]['message']['content']
                 logger.info(f"Successfully received response from {LLM_PROVIDER}.")
                 return llm_result
             else:
                  logger.warning(f"DeepSeek API response format unexpected: {response_data}")
                  return "DeepSeek API 返回格式错误或无有效内容。"
        else:
            return f"错误：不支持的 LLM 提供商 '{LLM_PROVIDER}'。"

    except ImportError as ie:
         logger.error(f"Missing library for {LLM_PROVIDER}. Please install it. {ie}")
         return f"错误：缺少用于 {LLM_PROVIDER} 的库，请安装。"
    except Exception as e:
        logger.error(f"Error calling LLM API ({LLM_PROVIDER}): {e}\n{traceback.format_exc()}")
        return f"调用 LLM API 时出错: {str(e)}"
