import os
import json
import base64
import io
from typing import Optional
from PIL import Image

import pandas as pd
import matplotlib.pyplot as plt
import torch
from fastapi import HTTPException
from chronos import BaseChronosPipeline
from jwt_utils import verify_token

class NOCFOAdapter:
    def __init__(self, json_path: Optional[str] = None):
        self.json_path = json_path or self._default_path()
        self.data = self._load_data()
        self.pipeline = BaseChronosPipeline.from_pretrained(
            "amazon/chronos-t5-small",
            device_map="cpu",
            torch_dtype=torch.float32,
        )

    def _default_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(os.path.dirname(current_dir), "NOCFO.json")

    def _load_data(self):
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def get_company_financials_from_token(self, report_type: str, token: Optional[str]) -> dict:
        if not token:
            return {"error": "Authentication token is required"}
        try:
            user_info = verify_token(token)
            company_id = user_info["company_id"]
        except HTTPException as e:
            return {"error": f"Authentication failed: {e.detail}"}

        if company_id not in self.data:
            return {"error": f"Company '{company_id}' not found"}

        if report_type == "all":
            return {company_id: self.data[company_id]}
        elif report_type in self.data[company_id]:
            return {company_id: {report_type: self.data[company_id][report_type]}}
        else:
            return {"error": f"Report type '{report_type}' not found for {company_id}"}

    def request_company_data_with_token(self, company_id: str, report_type: str, token: Optional[str]) -> dict:
        if not token:
            return {"error": "Authentication token is required"}
        try:
            user_info = verify_token(token)
            authorized_company = user_info["company_id"]
            if company_id != authorized_company:
                return {
                    "error": "Access denied",
                    "message": f"You are authorized to access data for {authorized_company} only. You do not have permission to access data for {company_id}."
                }
        except HTTPException as e:
            return {"error": f"Authentication failed: {e.detail}"}

        if company_id not in self.data:
            return {"error": f"Company '{company_id}' not found"}

        if report_type == "all":
            return {company_id: self.data[company_id]}
        elif report_type in self.data[company_id]:
            return {company_id: {report_type: self.data[company_id][report_type]}}
        else:
            return {"error": f"Report type '{report_type}' not found for {company_id}"}

# ================================================================================================
# Chronos related function
# ================================================================================================
    def extract_metric_series(self, company_data: dict, metric: str) -> pd.Series:
        ledger = company_data.get("ledger", [])
        series = []
        for acc in ledger:
            acc_key = acc["account_name"].lower().replace(" ", "_")
            if metric in acc_key:

                for entry in sorted(acc["entries"], key=lambda x: x["date"]):
                    net = entry.get("debet", 0) - entry.get("credit", 0)
                    series.append(net)
        return pd.Series(series)

    def format_metric_name(self, metric: str) -> str:
        return metric.replace("_", " ").title()

    def forecast_company_metric(self, company_name: str, metric: str, forecast_periods: int = 12) -> dict:
        company = self.data.get(company_name)
        if not company:
            raise ValueError(f"Company '{company_name}' not found in data.")

        normalized_metric = metric.lower().replace(" ", "_")
        ts = self.extract_metric_series(company, normalized_metric)
        if len(ts) < 10:
            raise ValueError(f"Chronos model requires at least 10 historical time points, but only {len(ts)} were found.")

        ledger_entries = []
        for acc in company.get("ledger", []):
            acc_key = acc["account_name"].lower().replace(" ", "_")
            if acc_key == normalized_metric:
                ledger_entries = sorted(acc["entries"], key=lambda x: x["date"])
                break

        if len(ledger_entries) < len(ts):
            raise ValueError("Mismatch between extracted time series and ledger entries.")

        start_date = pd.to_datetime(ledger_entries[0]["date"])
        history_index = pd.date_range(start=start_date, periods=len(ts), freq="MS")
        forecast_index = pd.date_range(start=history_index[-1] + pd.offsets.MonthBegin(), periods=forecast_periods, freq="MS")

        context = torch.tensor(ts.values, dtype=torch.float32)
        quantiles, _ = self.pipeline.predict_quantiles(
            context=context,
            prediction_length=forecast_periods,
            quantile_levels=[0.1, 0.5, 0.9],
        )

        low, median, high = quantiles[0, :, 0], quantiles[0, :, 1], quantiles[0, :, 2]


        plt.figure(figsize=(5, 2))
        plt.plot(history_index, ts, label="History", color="royalblue", linewidth=2)
        plt.plot(forecast_index, median, label="Forecast (median)", color="tomato", linewidth=2)
        plt.fill_between(forecast_index, low, high, color="tomato", alpha=0.3, label="Prediction Interval")
        plt.title(f"{company_name} – Forecast of '{self.format_metric_name(metric)}'", fontsize=12)
        plt.ylabel("Amount", fontsize=10)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()


        png_buf = io.BytesIO()
        plt.savefig(png_buf, format="png", dpi=40, bbox_inches='tight', pad_inches=0.01)
        plt.close()
        png_buf.seek(0)


        image = Image.open(png_buf).convert("RGB")
        jpeg_buf = io.BytesIO()
        image.save(jpeg_buf, format="JPEG", quality=25, optimize=True)

        plot_base64 = base64.b64encode(jpeg_buf.getvalue()).decode("utf-8")


        return {
    "historical": ts.tolist(),
    "forecast": median.tolist(),
    "plot_base64": plot_base64
}




