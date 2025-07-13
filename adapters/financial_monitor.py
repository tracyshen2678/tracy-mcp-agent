import json
import pandas as pd
import torch
from datetime import datetime, timedelta
from chronos import BaseChronosPipeline
from dateutil.relativedelta import relativedelta
import calendar

class FinancialMonitorAdapter:
    def __init__(self, company_data_path="NOCFO.json"):
        self.accounts = {
            1910: "Bank Account",
            4000: "Revenue Account",
            6000: "Expense Account"
        }
        self.company_data_path = company_data_path
        self.company_data = None
        self.company_name = None

    def set_company(self, company_name: str):
        with open(self.company_data_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        if company_name not in all_data:
            raise ValueError(f"Company '{company_name}' not found in data")
        self.company_data = all_data[company_name]
        self.company_name = company_name

    def load_company_df(self):
        records = []
        for account_data in self.company_data.get("ledger", []):
            account_number = int(account_data.get("account_number"))
            for entry in account_data.get("entries", []):
                if "date" in entry and entry["date"] is not None:
                    debit_value = float(entry.get("debit", entry.get("debet", 0)))
                    credit_value = float(entry.get("credit", 0))
                    records.append({
                        "date": entry["date"],
                        "account_number": account_number,
                        "net_flow": credit_value - debit_value
                    })
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
        return df

    def _aggregate_by_month(self, df):
        if df.empty:
            return pd.Series(dtype=float)
        monthly_sum = df.groupby('month')['net_flow'].sum()

        if not monthly_sum.empty:
            start_month = monthly_sum.index.min()
            end_month = monthly_sum.index.max()
            full_month_range = pd.date_range(start=start_month, end=end_month, freq='MS') # MS for Month Start
            monthly_sum = monthly_sum.reindex(full_month_range, fill_value=0)

        return monthly_sum

    def prepare_forecast_data(self, df):
        last_day_of_prev_month = datetime.now().replace(day=1) - timedelta(days=1)
        hist_df = df[df['date'] <= last_day_of_prev_month]

        ts_data = {}
        for acc in self.accounts:
            acc_df = hist_df[hist_df['account_number'] == acc]
            monthly_series = self._aggregate_by_month(acc_df)
            ts_data[acc] = monthly_series

        return ts_data

    def run_forecast(self, ts_data, prediction_length=3):
        valid_ts_data = {k: v for k, v in ts_data.items() if len(v) > 3}
        if not valid_ts_data:
            print("Warning: No accounts have sufficient historical months for forecasting.")
            return {acc: [] for acc in self.accounts}

        pipeline = BaseChronosPipeline.from_pretrained("amazon/chronos-t5-small")
        contexts = [torch.tensor(v.values, dtype=torch.float32) for v in valid_ts_data.values()]
        padded = torch.nn.utils.rnn.pad_sequence(contexts, batch_first=True)

        print("Running Chronos prediction (monthly)...")
        forecast = pipeline.predict(padded, prediction_length=prediction_length, num_samples=20)

        result = {}
        for i, acc in enumerate(valid_ts_data.keys()):
            result[acc] = forecast[i].mean(dim=0).tolist()
        for acc in self.accounts:
            if acc not in result:
                result[acc] = [0] * prediction_length
        return result

    def get_actuals(self, df, prediction_length=3):
        start_date = (datetime.now().replace(day=1) - relativedelta(months=prediction_length - 1)).date()
        end_date = datetime.now().date()

        recent_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
        actuals = {}

        for acc in self.accounts:
            acc_df = recent_df[recent_df['account_number'] == acc]
            monthly_series = self._aggregate_by_month(acc_df)
            actuals[acc] = monthly_series

        return actuals

    def compare(self, forecast, actuals):
        comparison = {}
        all_actuals_series = [s for s in actuals.values() if not s.empty]
        if not all_actuals_series:
            return {acc: [] for acc in self.accounts}
        start_month_ts = min(s.index.min() for s in all_actuals_series)

        for acc in self.accounts:
            acc_forecast = forecast.get(acc, [])
            acc_actuals = actuals.get(acc, pd.Series(dtype=float))

            compare_data = []
            for i in range(len(acc_forecast)):
                current_month_ts = start_month_ts + relativedelta(months=i)
                actual_val = acc_actuals.get(current_month_ts, 0)
                pred_val_full_month = acc_forecast[i]
                pred_val_adjusted = pred_val_full_month
                today = datetime.now()
                if current_month_ts.year == today.year and current_month_ts.month == today.month:
                    days_in_month = calendar.monthrange(today.year, today.month)[1]
                    days_passed = today.day
                    proportion_of_month = days_passed / days_in_month
                    pred_val_adjusted = pred_val_full_month * proportion_of_month

                deviation = actual_val - pred_val_adjusted
                pct = (deviation / pred_val_adjusted) * 100 if pred_val_adjusted != 0 else float('inf') if actual_val != 0 else 0

                compare_data.append({
                    "month": current_month_ts.strftime('%Y-%m'),
                    "actual": actual_val,
                    "forecast": pred_val_adjusted,
                    "deviation_pct": round(pct, 2)
                })
            comparison[acc] = compare_data
        return comparison

    def generate_text_summary(self, comparison):
        """生成结构化的文本摘要"""
        text = "## Monthly Financial Health Summary\n"
        for acc in self.accounts:
            text += f"\n### {self.accounts[acc]}\n"
            comp_data = comparison.get(acc, [])
            if comp_data:
                for x in comp_data:
                    flag = " 🚨" if abs(x.get('deviation_pct', 0)) > 20 else ""
                    text += f"- {x['month']}: Actual={x['actual']:,.2f}, Forecast={x['forecast']:,.2f}, Deviation={x['deviation_pct']:.2f}%{flag}\n"
            else:
                text += "No data for comparison.\n"
        return text

    def run_monitoring(self, company_id: str):
        print(f"Starting MONTHLY monitoring for company: {company_id}")
        self.set_company(company_id)

        print("Loading and aggregating data by month...")
        df = self.load_company_df()

        print("Preparing monthly forecast data...")
        ts_data = self.prepare_forecast_data(df)

        PREDICTION_MONTHS = 3
        print(f"Running forecast for the next {PREDICTION_MONTHS} months...")
        forecast = self.run_forecast(ts_data, prediction_length=PREDICTION_MONTHS)

        print("Getting actuals for recent months...")
        actuals = self.get_actuals(df, prediction_length=PREDICTION_MONTHS)

        print("Comparing forecast and actuals...")
        comparison = self.compare(forecast, actuals)

        print("Generating text summary...")
        summary = self.generate_text_summary(comparison)

        print("Monitoring finished. Returning raw data.")

        return {"summary": summary, "comparison_data": comparison}