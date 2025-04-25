def get_recommendation(premium):
    """根据溢价率获取投资建议"""
    if premium > 30:
        return "强烈买入"
    elif premium > 15:
        return "买入"
    elif premium > -10:
        return "持有"
    elif premium > -30:
        return "减持"
    else:
        return "强烈卖出"
