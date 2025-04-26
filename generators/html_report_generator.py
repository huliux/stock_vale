from .base_report_generator import BaseReportGenerator
import os
import numpy as np

def get_recommendation(premium):
    """根据溢价率返回投资建议"""
    if premium > 20:
        return "强烈买入"
    elif premium > 10:
        return "买入"
    elif premium > -10:
        return "持有"
    elif premium > -20:
        return "卖出"
    else:
        return "强烈卖出"

class HtmlReportGenerator(BaseReportGenerator):
    def __init__(self, stock_data):
        super().__init__(stock_data)
        self.stock_info = stock_data.stock_info
        self.stock_code = stock_data.stock_info.get('ts_code', 'N/A')
        self.stock_name = stock_data.stock_info.get('name', '未知名称')

    def export_report(self):
        """导出HTML报告到文件"""
        html_content = self.generate_html_report()
        os.makedirs('reports', exist_ok=True)
        filename = f"reports/{self.stock_code}_valuation_report.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return filename
        except IOError as e:
            raise RuntimeError(f"导出HTML报告失败: {str(e)}")

    def generate_html_report(self):
        """生成HTML报告，确保与Markdown报告使用相同的数据和计算逻辑"""
        from datetime import datetime
        
        # 使用基类方法获取相同的数据
        pe_vals = self._calculate_pe_valuations()
        pb_vals = self._calculate_pb_valuations()
        ev_vals = self._calculate_ev_valuations()
        
        # 基本信息 - 与Markdown报告保持一致
        basic_info = f"""
        <div class="container">
            <h1>股票估值报告 - {self.stock_code} {self.stock_name}</h1>
            <p><em>生成日期: {datetime.now().strftime('%Y年%m月%d日')}</em></p>
            
            <h2>基本信息</h2>
            <table>
                <tr>
                    <th>项目</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td>股票代码</td>
                    <td>{self.stock_code}</td>
                </tr>
                <tr>
                    <td>股票名称</td>
                    <td>{self.stock_name}</td>
                </tr>
                <tr>
                    <td>当前价格</td>
                    <td>{self.stock_data.latest_price:.2f} 元</td>
                </tr>
                <tr>
                    <td>总股本</td>
                    <td>{self.stock_data.total_shares/100000000:.2f} 亿股</td>
                </tr>
                <tr>
                    <td>市值</td>
                    <td>{self.stock_data.market_cap:.2f} 亿元</td>
                </tr>
            </table>
        """

        # 相对估值
        relative_valuation = """
            <h2>相对估值</h2>
            
            <h3>PE估值</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        for pe in self.stock_data.pe_range:
            value = float(pe) * (self.stock_data.latest_fcff / 100000000) / (self.stock_data.total_shares / 100000000)
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            relative_valuation += f"""
                <tr>
                    <td>PE={pe}</td>
                    <td>{value:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                </tr>
            """
        
        relative_valuation += """
            </table>
            
            <h3>PB估值</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        for pb in self.stock_data.pb_range:
            value = float(pb) * self.stock_data.latest_price / self.stock_data.pb_history
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            relative_valuation += f"""
                <tr>
                    <td>PB={pb}</td>
                    <td>{value:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                </tr>
            """
        
        relative_valuation += """
            </table>
            
            <h3>EV/EBITDA估值</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        for multiple in self.stock_data.ev_ebitda_range:
            value = (float(multiple) * self.stock_data.ebitda - (self.stock_data.enterprise_value - self.stock_data.market_cap * 100000000)) / self.stock_data.total_shares
            premium = (value - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            relative_valuation += f"""
                <tr>
                    <td>EV/EBITDA={multiple}</td>
                    <td>{value:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                </tr>
            """
        
        relative_valuation += """
            </table>
        """

        # 绝对估值
        absolute_valuation = """
            <h2>绝对估值</h2>
            
            <h3>DCF估值(FCFF基本资本性支出)</h3>
            <table>
                <tr>
                    <th>增长率</th>
                    <th>折现率</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        if self.stock_data.fcff_vals:
            for val in self.stock_data.fcff_vals:
                absolute_valuation += f"""
                <tr>
                    <td>{val['growth_rate']:.1%}</td>
                    <td>{val['discount_rate']:.1%}</td>
                    <td>{val['value']:.2f} 元/股</td>
                    <td>{val['premium']:+.2f}%</td>
                </tr>
                """
        else:
            absolute_valuation += """
                <tr>
                    <td colspan="4">FCFF为负或零，无法进行DCF估值</td>
                </tr>
            """
        
        absolute_valuation += """
            </table>
            
            <h3>DCF估值(FCFF完整资本性支出)</h3>
            <table>
                <tr>
                    <th>增长率</th>
                    <th>折现率</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        if self.stock_data.fcff_full_vals:
            for val in self.stock_data.fcff_full_vals:
                absolute_valuation += f"""
                <tr>
                    <td>{val['growth_rate']:.1%}</td>
                    <td>{val['discount_rate']:.1%}</td>
                    <td>{val['value']:.2f} 元/股</td>
                    <td>{val['premium']:+.2f}%</td>
                </tr>
                """
        else:
            absolute_valuation += """
                <tr>
                    <td colspan="4">FCFF为负或零，无法进行DCF估值</td>
                </tr>
            """
        
        absolute_valuation += """
            </table>
            
            <h3>DDM估值(股利贴现模型)</h3>
            <table>
                <tr>
                    <th>增长率</th>
                    <th>折现率</th>
                    <th>估值</th>
                    <th>相对当前价格</th>
                </tr>
        """
        if self.stock_data.ddm_vals:
            for val in self.stock_data.ddm_vals:
                absolute_valuation += f"""
                <tr>
                    <td>{val['growth_rate']:.1%}</td>
                    <td>{val['discount_rate']:.1%}</td>
                    <td>{val['value']:.2f} 元/股</td>
                    <td>{val['premium']:+.2f}%</td>
                </tr>
                """
        else:
            absolute_valuation += """
                <tr>
                    <td colspan="4">无有效分红数据，无法进行DDM估值</td>
                </tr>
            """
        
        absolute_valuation += """
            </table>
        """

        # 其他分析
        other_analysis = f"""
            <h2>其他分析</h2>
            
            <h3>股息分析</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td>当前股息率</td>
                    <td>{self.stock_data.current_yield:.2f}%</td>
                </tr>
                <tr>
                    <td>3年平均分红</td>
                    <td>{self.stock_data.avg_div:.2f} 元/股</td>
                </tr>
                <tr>
                    <td>分红支付率</td>
                    <td>{self.stock_data.payout_ratio:.2f}%</td>
                </tr>
            </table>
            
            <h3>增长分析</h3>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td>3年净利润CAGR</td>
                    <td>{self.stock_data.cagr.get('income_3y', 0):.2f}%</td>
                </tr>
                <tr>
                    <td>3年营收CAGR</td>
                    <td>{self.stock_data.cagr.get('revenue_3y', 0):.2f}%</td>
                </tr>
            </table>
        """

        # 收集所有估值结果
        all_valuations = []
        
        # PE估值 - 使用基类计算方法
        for val in pe_vals:
            all_valuations.append(val['value'])
        
        # PB估值 - 使用基类计算方法
        for val in pb_vals:
            all_valuations.append(val['value'])
        
        # EV/EBITDA估值 - 使用基类计算方法
        for val in ev_vals:
            all_valuations.append(val['value'])
        
        # DCF估值 (FCFF基本版)
        if self.stock_data.fcff_vals:
            for val in self.stock_data.fcff_vals:
                all_valuations.append(val['value'])
        
        # DCF估值 (FCFF完整版)
        if self.stock_data.fcff_full_vals:
            for val in self.stock_data.fcff_full_vals:
                all_valuations.append(val['value'])
        
        # DCF估值 (FCFE基本版)
        if self.stock_data.fcfe_vals:
            for val in self.stock_data.fcfe_vals:
                all_valuations.append(val['value'])
        
        # DCF估值 (FCFE完整版)
        if self.stock_data.fcfe_full_vals:
            for val in self.stock_data.fcfe_full_vals:
                all_valuations.append(val['value'])
        
        # DDM估值
        if self.stock_data.ddm_vals:
            for val in self.stock_data.ddm_vals:
                all_valuations.append(val['value'])
        
        # 综合分析
        if not all_valuations:
            valuation_range = "无法计算估值区间"
        else:
            valuation_range = f"{min(all_valuations):.2f} - {max(all_valuations):.2f} 元/股"
            
        comprehensive_analysis = f"""
            <h2>综合分析</h2>
            
            <p><strong>估值区间: {valuation_range}</strong></p>
            <p><strong>当前价格: {self.stock_data.latest_price:.2f} 元/股</strong></p>
            
            <h3>六种估值组合</h3>
            <table>
                <tr>
                    <th>组合</th>
                    <th>综合估值</th>
                    <th>相对当前价格</th>
                    <th>投资建议</th>
                </tr>
        """
        # 1. 全部方法
        weights_all = {
            'DCF(FCFF基本)': 0.1, 'DCF(FCFE基本)': 0.1,
            'DCF(FCFF完整)': 0.1, 'DCF(FCFE完整)': 0.1,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        # 计算各方法的中位数
        method_medians = {}
        
        # 从stock_data获取估值数据
        pe_vals = self._calculate_pe_valuations()
        pb_vals = self._calculate_pb_valuations()
        ev_vals = self._calculate_ev_valuations()
        fcff_vals = self.stock_data.fcff_vals or []
        fcff_full_vals = self.stock_data.fcff_full_vals or []
        fcfe_vals = self.stock_data.fcfe_vals or []
        fcfe_full_vals = self.stock_data.fcfe_full_vals or []
        ddm_vals = self.stock_data.ddm_vals or []
        
        # 计算中位数
        if pe_vals:
            pe_values = [v['value'] for v in pe_vals if 'value' in v]
            if pe_values:
                method_medians['PE'] = np.median(pe_values)
        if pb_vals:
            pb_values = [v['value'] for v in pb_vals if 'value' in v]
            if pb_values:
                method_medians['PB'] = np.median(pb_values)
        if fcff_vals:
            fcff_values = [v['value'] for v in fcff_vals if 'value' in v]
            if fcff_values:
                method_medians['DCF(FCFF基本)'] = np.median(fcff_values)
        if fcff_full_vals:
            fcff_full_values = [v['value'] for v in fcff_full_vals if 'value' in v]
            if fcff_full_values:
                method_medians['DCF(FCFF完整)'] = np.median(fcff_full_values)
        if fcfe_vals:
            fcfe_values = [v['value'] for v in fcfe_vals if 'value' in v]
            if fcfe_values:
                method_medians['DCF(FCFE基本)'] = np.median(fcfe_values)
        if fcfe_full_vals:
            fcfe_full_values = [v['value'] for v in fcfe_full_vals if 'value' in v]
            if fcfe_full_values:
                method_medians['DCF(FCFE完整)'] = np.median(fcfe_full_values)
        if ddm_vals:
            ddm_values = [v['value'] for v in ddm_vals if 'value' in v]
            if ddm_values:
                method_medians['DDM'] = np.median(ddm_values)
        if ev_vals:
            ev_values = [v['value'] for v in ev_vals if 'value' in v]
            if ev_values:
                method_medians['EV/EBITDA'] = np.median(ev_values)

        weighted_sum = sum(v * weights_all.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_all.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合1 (综合)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """

        # 2. 完整版DCF + 传统方法
        weights_full_dcf = {
            'DCF(FCFF完整)': 0.2, 'DCF(FCFE完整)': 0.2,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        weighted_sum = sum(v * weights_full_dcf.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_full_dcf.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合2 (绝对（完整） + 相对)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """

        # 3. 基本版DCF + 传统方法
        weights_basic_dcf = {
            'DCF(FCFF基本)': 0.2, 'DCF(FCFE基本)': 0.2,
            'DDM': 0.2, 'PE': 0.15, 'PB': 0.1, 'EV/EBITDA': 0.15
        }
        weighted_sum = sum(v * weights_basic_dcf.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_basic_dcf.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合3 (绝对（基本） + 相对)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """

        # 4. 仅完整版DCF + DDM
        weights_full_dcf_ddm = {
            'DCF(FCFF完整)': 0.4, 'DCF(FCFE完整)': 0.4, 'DDM': 0.2
        }
        weighted_sum = sum(v * weights_full_dcf_ddm.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_full_dcf_ddm.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合4 (绝对（完整） + 股息)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """

        # 5. 仅基本版DCF + DDM
        weights_basic_dcf_ddm = {
            'DCF(FCFF基本)': 0.4, 'DCF(FCFE基本)': 0.4, 'DDM': 0.2
        }
        weighted_sum = sum(v * weights_basic_dcf_ddm.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_basic_dcf_ddm.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合5 (绝对（基本） + 股息)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """

        # 6. 仅传统估值方法
        weights_traditional = {
            'PE': 0.4, 'PB': 0.3, 'EV/EBITDA': 0.3
        }
        weighted_sum = sum(v * weights_traditional.get(k, 0) for k, v in method_medians.items())
        total_weight = sum(weights_traditional.values())
        
        if total_weight > 0:
            weighted_avg = weighted_sum / total_weight
            premium = (weighted_avg - self.stock_data.latest_price) / self.stock_data.latest_price * 100
            recommendation = get_recommendation(premium)
            comprehensive_analysis += f"""
                <tr>
                    <td>组合6 (相对)</td>
                    <td>{weighted_avg:.2f} 元/股</td>
                    <td>{premium:+.2f}%</td>
                    <td>{recommendation}</td>
                </tr>
            """
        
        comprehensive_analysis += """
            </table>
        </div>
        """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>股票估值报告 - {self.stock_code}</title>
            <style>
                /* Apple Design风格优化版 */
                :root {{
                    --primary-color: #0071e3;
                    --background-color: #f5f5f7;
                    --text-color: #1d1d1f;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell;
                    margin: 2rem;
                    color: var(--text-color);
                    background-color: var(--background-color);
                }}
                .container {{
                    max-width: 980px;
                    margin: 0 auto;
                    background: white;
                    padding: 2rem;
                    border-radius: 18px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 2rem 0;
                }}
                th {{
                    background-color: var(--background-color);
                    color: var(--text-color);
                    padding: 1rem;
                    border-bottom: 2px solid #d2d2d7;
                }}
                td {{
                    padding: 1rem;
                    border-bottom: 1px solid #d2d2d7;
                }}
                .chart-container {{
                    margin: 2rem 0;
                    height: 400px;
                }}
            </style>
        </head>
        <body>
            {basic_info}
            {relative_valuation}
            {absolute_valuation}
            {other_analysis}
            {comprehensive_analysis}
        </body>
        </html>
        """
        return html_content
