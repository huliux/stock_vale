# 股票估值计算工具

## 功能概述

该工具用于计算和生成股票的绝对估值报告。具体功能包括：

- **PE估值**: 根据不同的PE倍数计算股票的估值。
- **PB估值**: 根据不同的PB倍数计算股票的估值。
- **DCF估值 (FCFF)**: 使用自由现金流贴现模型（FCFF）计算股票的估值。
- **DCF估值 (FCFE)**: 使用股权自由现金流贴现模型（FCFE）计算股票的估值。
- **EV/EBITDA估值**: 根据不同的EV/EBITDA倍数计算股票的估值。
- **股息分析**: 分析股票的股息情况，包括股息率、3年平均分红和分红支付率。
- **增长分析**: 分析股票的净利润和营收的复合年增长率（CAGR）。
- **DDM估值**: 使用股利贴现模型（DDM）计算股票的估值。
- **综合分析**: 结合多种估值方法，生成综合估值报告，并提供投资建议。

## 使用方法

1. **安装依赖**

   首先，确保你已经安装了项目所需的依赖项。你可以使用以下命令安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. **运行程序**

   使用以下命令运行主程序：

   ```bash
   python main.py --stock <股票代码> --pe <PE倍数范围> --pb <PB倍数范围> --growth <增长率范围> --discount <折现率范围> --ev-ebitda <EV/EBITDA倍数范围>
   ```

   例如：

   ```bash
   python main.py --stock 600104.SH --pe 5,8,12 --pb 0.8,1.2,1.5 --growth 0.05,0.08,0.1 --discount 0.1,0.12,0.15 --ev-ebitda 6,8,10
   ```

   运行后，程序将生成一个文本格式的估值报告，并保存在一个Markdown文件中。

## 依赖项

项目所需的依赖项已列在 `requirements.txt` 文件中：

- `matplotlib==3.10.1`
- `numpy==1.23.5`
- `pandas==2.2.3`
- `SQLAlchemy==2.0.40`

## 代码结构

- `main.py`: 主程序入口，负责解析命令行参数、获取数据、计算估值并生成报告。
- `data_fetcher.py`: 从数据库中获取股票的基本信息、最新价格、总股本、财务数据和分红数据。
- `valuation_calculator.py`: 计算各种估值指标，包括PE比率、PB比率、增长率、DCF估值、EV/EBITDA估值和DDM估值。
- `report_generator.py`: 生成不同格式的股票估值报告，包括文本格式和Markdown格式。
- `models/stock_data.py`: 定义 `StockData` 类，用于封装股票的所有相关信息。
- `generators/text_report_generator.py`: 生成文本格式的估值报告。
- `generators/markdown_report_generator.py`: 生成Markdown格式的估值报告。
- `utils/report_utils.py`: 包含报告生成的辅助函数和工具。

## 贡献

欢迎贡献代码和提出建议。请遵循以下步骤：

1. Fork 项目。
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 打开一个 Pull Request。

## 许可证

该项目采用 [MIT 许可证](LICENSE)。

## 联系方式

- **作者**: Forest
- **邮箱**: forest@example.com
