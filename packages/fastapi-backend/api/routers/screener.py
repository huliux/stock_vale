from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional
import logging
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
        if request_body.pe_min is not None:
            filtered_df = filtered_df[filtered_df['pe_ttm'] >= request_body.pe_min]
        if request_body.pe_max is not None:
            filtered_df = filtered_df[filtered_df['pe_ttm'] <= request_body.pe_max]
        if request_body.pb_min is not None:
            filtered_df = filtered_df[filtered_df['pb'] >= request_body.pb_min]
        if request_body.pb_max is not None:
            filtered_df = filtered_df[filtered_df['pb'] <= request_body.pb_max]
        if request_body.market_cap_min is not None: # 前端发送的是亿元
            filtered_df = filtered_df[filtered_df['market_cap_billion'] >= request_body.market_cap_min]
        if request_body.market_cap_max is not None: # 前端发送的是亿元
            filtered_df = filtered_df[filtered_df['market_cap_billion'] <= request_body.market_cap_max]
        
        # 移除PE/PB为负或极大的异常值 (可选，但推荐)
        filtered_df = filtered_df[filtered_df['pe_ttm'] > 0]
        # filtered_df = filtered_df[filtered_df['pb'] > 0] # PB可以为负，视情况而定

        total_results = len(filtered_df)
        
        # TODO: 实现分页逻辑 (如果前端支持并发送 page 和 page_size)
        # current_page = request_body.page or 1
        # page_size = request_body.page_size or 20
        # start_index = (current_page - 1) * page_size
        # end_index = start_index + page_size
        # paged_df = filtered_df.iloc[start_index:end_index]
        paged_df = filtered_df # 暂时不分页

        # Log sample of paged_df before converting to dicts
        if not paged_df.empty:
            logger.info(f"Paged DataFrame 样本 (前3行，关注 close, market_cap_billion):\n{paged_df[['ts_code', 'name', 'close', 'market_cap_billion']].head(3)}")

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
                model_instance = ApiScreenedStockModel(**row_data)
                results.append(model_instance)
            except Exception as pydantic_exc:
                logger.error(f"Pydantic 模型转换错误，行索引 {row_idx}，数据: {row_data}, 错误: {pydantic_exc}")
                # Optionally, append a default/error model or skip
                # For now, let's re-raise if critical, or log and continue if some can be salvaged
                # Depending on strictness, this could be a place to add more robust error handling
                # For now, if one fails, the whole request might fail due to the list comprehension style before.
                # This loop allows individual logging.
                # If a row fails validation, it won't be added to results.
                # Consider if this is the desired behavior or if an error should be raised.
                pass # Silently skip problematic rows for now, or handle as needed

        # Log sample of results (list of Pydantic models)
        if results:
            logger.info(f"转换后的 Pydantic 模型列表样本 (前2条记录中关注 latest_price, total_market_cap):")
            for i, model_sample in enumerate(results[:2]):
                 logger.info(f"模型 {i}: ts_code={model_sample.ts_code}, name={model_sample.name}, latest_price={model_sample.latest_price}, total_market_cap={model_sample.total_market_cap}")
        
        logger.info(f"筛选完成，返回 {len(results)} 条记录 (总计 {total_results} 条)。")
        return ApiStockScreenerResponseModel(
            results=results, 
            total=total_results,
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
            stock_screener_service.load_stock_basic(force_update=True)
            logger.info("股票基本信息已触发更新。")
        
        if request_body.data_type == 'daily' or request_body.data_type == 'all':
            # 更新每日数据通常需要一个最新的交易日
            trade_date = stock_screener_service.get_latest_valid_trade_date()
            stock_screener_service.load_daily_basic(trade_date=trade_date, force_update=True)
            logger.info(f"交易日 {trade_date} 的每日行情指标已触发更新。")

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
