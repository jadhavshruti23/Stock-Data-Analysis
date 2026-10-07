# Stock Data Analysis and Forecasting

## Project Overview
This project performs end-to-end stock market data analysis and forecasting using Python and Power BI.

The project is designed as a reusable stock-analysis workflow that can work with different historical stock datasets rather than being limited to a single company.

The workflow covers:

- Data loading and automatic column detection
- Data cleaning and validation
- Exploratory Data Analysis (EDA)
- Technical feature engineering
- Stock performance and risk analysis
- Machine learning-based forecasting
- Model comparison and evaluation
- Power BI dashboard development

---

## Project Objectives

The main objectives of this project are:

1.Clean and validate historical stock market data.
2.Analyze stock price movements and trading activity.
3.Calculate useful technical indicators and risk measures.
4.Build machine learning models for next-trading-day price prediction.
5.Compare forecasting models using MAE, RMSE and MAPE.
6.Create an interactive Power BI dashboard.
7.Generate reusable outputs that can be used for further analysis.

---

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- Statsmodels
- OpenPyXL
- Power BI
- Git & GitHub

---

## Project Structure

```text
Stock-Data-Analysis/
│
├── apl_stock.xlsx
├── sys.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── outputs/
    ├── cleaned_data/
    │   ├── cleaned_stock_data.csv
    │   └── stock_features.csv
    │
    ├── forecasts/
    │   ├── forecast_results.csv
    │   ├── model_comparison.csv
    │   └── feature_importance.csv
    │
    └── powerbi_stock_data.csv