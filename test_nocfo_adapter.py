from adapters.NOCFO_adapter import NOCFOAdapter
import base64
import matplotlib.pyplot as plt
from io import BytesIO


nocfo = NOCFOAdapter()


COMPANY = "TechNova"
METRIC = "cash_and_equivalents"

def test_forecast_financials():
    print("=== Testing forecast_financials ===")
    try:
        result = nocfo.forecast_company_metric(COMPANY, METRIC, forecast_periods=12)
        print("[✅] Forecast generated successfully.")
        print("Historical series:", result["historical"])
        print("Forecast median:", result["forecast"])


        image_data = base64.b64decode(result["plot_base64"])
        image = BytesIO(image_data)
        plt.imshow(plt.imread(image))
        plt.axis('off')
        plt.title(f"{COMPANY} – {METRIC} Forecast")
        plt.show()

    except Exception as e:
        print("[❌] Forecast failed with error:", str(e))


if __name__ == "__main__":
    test_forecast_financials()