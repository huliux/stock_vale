from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional
import logging
import math
from datetime import datetime # Import datetime

# Try absolute import from the perspective of 'packages/fastapi-backend' as root
from services import stock_screener_service
from api.models import ( # Assuming models.py is in 'api' directory, relative to 'services' this is api.models
    ApiStockScreenerRequestModel,
    ApiStockScreenerResponseModel,
    ApiUpdateScreenerDataRequestModel,
    ApiUpdateScreenerDataResponseModel,
    ApiScreenedStockModel
)

router = APIRouter(
    prefix="/screener",
    tags=["screener"],
)

logger = logging.getLogger(__name__)

@router.post("/stocks", response_model=ApiStockScreenerResponseModel)
async def get_screened_stocks(
    request_body: ApiStockScreenerRequestModel = Body(...)
):
    """
    根据筛选条件获取股票列表。
    """
    try:
        logger.info(f"收到股票筛选请求: {request_body.model_dump(exclude_none=True)}")

        # 1. 获取最新有效交易日 (如果需要每次都获取最新，或者从缓存/配置中读取)
        #    对于筛选，通常使用最近已落盘的数据。
        trade_date = stock_screener_service.get_latest_valid_trade_date()

        # 2. 获取合并后的数据
        #    force_update 标志可以根据需要设置为True，例如用户触发了数据更新后
        merged_df = stock_screener_service.get_merged_stock_data(trade_date=trade_date)

        if merged_df is None or merged_df.empty:
            logger.warning("未能获取或合并股票数据用于筛选。")
            return ApiStockScreenerResponseModel(results=[], total=0, last_data_update_time=trade_date)

        # 3. 应用筛选条件
        filtered_df = merged_df.copy()

        # 基础财务指标筛选 - 增加对 NaN 值的处理
        if request_body.pe_min is not None:
            filtered_df = filtered_df[filtered_df['pe_ttm'].notna() & (filtered_df['pe_ttm'] >= request_body.pe_min)]
        if request_body.pe_max is not None:
            filtered_df = filtered_df[filtered_df['pe_ttm'].notna() & (filtered_df['pe_ttm'] <= request_body.pe_max)]
        if request_body.pb_min is not None:
            filtered_df = filtered_df[filtered_df['pb'].notna() & (filtered_df['pb'] >= request_body.pb_min)]
        if request_body.pb_max is not None:
            filtered_df = filtered_df[filtered_df['pb'].notna() & (filtered_df['pb'] <= request_body.pb_max)]
        if request_body.ps_min is not None:
            filtered_df = filtered_df[filtered_df['ps'].notna() & (filtered_df['ps'] >= request_body.ps_min)]
        if request_body.ps_max is not None:
            filtered_df = filtered_df[filtered_df['ps'].notna() & (filtered_df['ps'] <= request_body.ps_max)]
        if request_body.ps_ttm_min is not None:
            filtered_df = filtered_df[filtered_df['ps_ttm'].notna() & (filtered_df['ps_ttm'] >= request_body.ps_ttm_min)]
        if request_body.ps_ttm_max is not None:
            filtered_df = filtered_df[filtered_df['ps_ttm'].notna() & (filtered_df['ps_ttm'] <= request_body.ps_ttm_max)]

        # 市值筛选 - 增加对 NaN 值的处理
        if request_body.market_cap_min is not None: # 前端发送的是亿元
            filtered_df = filtered_df[filtered_df['market_cap_billion'].notna() & (filtered_df['market_cap_billion'] >= request_body.market_cap_min)]
        if request_body.market_cap_max is not None: # 前端发送的是亿元
            filtered_df = filtered_df[filtered_df['market_cap_billion'].notna() & (filtered_df['market_cap_billion'] <= request_body.market_cap_max)]

        # 记录筛选后的数据量
        logger.info(f"应用筛选条件后，剩余 {len(filtered_df)} 条记录。")

        # 行业筛选
        if request_body.industry is not None and request_body.industry != 'all' and 'industry' in filtered_df.columns:
            logger.info(f"应用行业筛选: {request_body.industry}")
            filtered_df = filtered_df[filtered_df['industry'] == request_body.industry]

        # 企业性质筛选
        if request_body.act_ent_type is not None and request_body.act_ent_type != 'all' and 'act_ent_type' in filtered_df.columns:
            logger.info(f"应用企业性质筛选: {request_body.act_ent_type}")
            filtered_df = filtered_df[filtered_df['act_ent_type'] == request_body.act_ent_type]

        # 注释掉默认的PE筛选，让用户完全控制筛选条件
        # filtered_df = filtered_df[filtered_df['pe_ttm'] > 0]
        # filtered_df = filtered_df[filtered_df['pb'] > 0] # PB可以为负，视情况而定

        total_results = len(filtered_df)

        # 实现分页逻辑
        current_page = request_body.page or 1
        page_size = request_body.page_size or 20

        # 如果有排序参数，可以在这里添加排序逻辑
        # 例如：filtered_df = filtered_df.sort_values(by='pe_ttm', ascending=True)

        # 计算分页索引
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size

        # 应用分页
        paged_df = filtered_df.iloc[start_index:min(end_index, len(filtered_df))]

        logger.info(f"分页: 第 {current_page} 页，每页 {page_size} 条，总计 {total_results} 条记录")

        # Log sample of paged_df before converting to dicts
        if not paged_df.empty:
            logger.info(f"Paged DataFrame 样本 (前3行，关注 close, market_cap_billion):\n{paged_df[['ts_code', 'name', 'close', 'market_cap_billion']].head(3)}")

        # 处理特殊浮点数值（Infinity, NaN）
        # 将 DataFrame 中的 inf, -inf, NaN 替换为 None
        paged_df = paged_df.replace([float('inf'), float('-inf'), float('nan')], None)

        records_list = paged_df.to_dict(orient='records')

        # Log sample of records_list (list of dicts)
        if records_list:
            logger.info(f"转换后的字典列表样本 (前2条记录中关注 close, market_cap_billion):")
            for i, record_sample in enumerate(records_list[:2]):
                sample_to_log = {k: record_sample.get(k) for k in ['ts_code', 'name', 'close', 'market_cap_billion']}
                logger.info(f"记录 {i}: {sample_to_log}")

        results = []
        for row_idx, row_data in enumerate(records_list):
            try:
                # 额外检查并处理特殊浮点数值
                sanitized_data = {}
                for key, value in row_data.items():
                    if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
                        sanitized_data[key] = None
                    else:
                        sanitized_data[key] = value

                model_instance = ApiScreenedStockModel(**sanitized_data)
                results.append(model_instance)
            except Exception as pydantic_exc:
                logger.error(f"Pydantic 模型转换错误，行索引 {row_idx}，数据: {row_data}, 错误: {pydantic_exc}")
                # 记录错误但继续处理其他行
                pass # Silently skip problematic rows for now, or handle as needed

        # Log sample of results (list of Pydantic models)
        if results:
            logger.info(f"转换后的 Pydantic 模型列表样本 (前2条记录中关注 latest_price, total_market_cap):")
            for i, model_sample in enumerate(results[:2]):
                 logger.info(f"模型 {i}: ts_code={model_sample.ts_code}, name={model_sample.name}, latest_price={model_sample.latest_price}, total_market_cap={model_sample.total_market_cap}")

        logger.info(f"筛选完成，返回 {len(results)} 条记录 (总计 {total_results} 条)。")

        # 确保返回的分页参数是整数
        try:
            current_page_int = int(current_page)
            page_size_int = int(page_size)
        except (ValueError, TypeError):
            current_page_int = 1
            page_size_int = 20
            logger.warning(f"分页参数转换为整数失败，使用默认值: page={current_page_int}, page_size={page_size_int}")

        return ApiStockScreenerResponseModel(
            results=results,
            total=total_results,
            page=current_page_int,
            page_size=page_size_int,
            last_data_update_time=trade_date # 可以考虑更精确的缓存文件时间
        )

    except stock_screener_service.StockScreenerServiceError as e:
        logger.error(f"股票筛选服务错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"处理股票筛选请求时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="处理股票筛选请求时发生内部错误。")


@router.post("/update-data", response_model=ApiUpdateScreenerDataResponseModel)
async def update_screener_data(
    request_body: ApiUpdateScreenerDataRequestModel = Body(...)
):
    """
    触发股票筛选器基础数据的更新。
    """
    try:
        logger.info(f"收到数据更新请求: {request_body.data_type}")

        if request_body.data_type == 'basic' or request_body.data_type == 'all':
            # 强制更新股票基本信息
            stock_basic_df = stock_screener_service.load_stock_basic(force_update=True)
            logger.info(f"股票基本信息已触发更新，获取到 {len(stock_basic_df)} 条记录。")

        if request_body.data_type == 'daily' or request_body.data_type == 'all':
            # 更新每日数据通常需要一个最新的交易日
            trade_date = stock_screener_service.get_latest_valid_trade_date()
            daily_basic_df = stock_screener_service.load_daily_basic(trade_date=trade_date, force_update=True)
            logger.info(f"交易日 {trade_date} 的每日行情指标已触发更新，获取到 {len(daily_basic_df)} 条记录。")

        # 如果是全部更新，也更新合并后的数据
        if request_body.data_type == 'all':
            # 强制更新合并数据
            trade_date = stock_screener_service.get_latest_valid_trade_date()
            merged_df = stock_screener_service.get_merged_stock_data(trade_date=trade_date, force_update_basic=True, force_update_daily=True)
            logger.info(f"合并数据已触发更新，合并后共有 {len(merged_df)} 条记录。")

        # TODO: 获取更精确的更新时间戳
        # Get actual timestamps AFTER updates are triggered
        actual_timestamps = stock_screener_service.get_cache_file_timestamps()

        return ApiUpdateScreenerDataResponseModel(
            status="success",
            message=f"数据更新任务 ({request_body.data_type}) 已成功触发。",
            last_update_times=actual_timestamps
        )
    except stock_screener_service.StockScreenerServiceError as e:
        logger.error(f"数据更新服务错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"处理数据更新请求时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="处理数据更新请求时发生内部错误。")
