import hashlib
import datetime
import os
import requests
import xml.etree.ElementTree as ET


class YTJAdapter:
    def __init__(self, customer_id: str = None, secret_key: str = None):
        self.customer_id = customer_id or os.getenv("YTJ_ID") or "NoCFO"
        self.secret_key = secret_key or os.getenv("YTJ_SECRET") or "E22DAD39-82FA-4930-8274-7FFA057611AD"
        self.endpoint = "https://api.tietopalvelu.ytj.fi/yritystiedot.asmx"

    def _generate_auth(self):
        timestamp = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        raw = f"{self.customer_id}{self.secret_key}{timestamp}"
        signature = hashlib.sha1(raw.encode("utf-8")).hexdigest().upper()
        return timestamp, signature

    def fetch_company_details(self, business_id: str):
        timestamp, signature = self._generate_auth()

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.ytj.fi/wmYritysTiedotV3",
        }

        body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <wmYritysTiedotV3 xmlns="http://www.ytj.fi/">
      <ytunnus>{business_id}</ytunnus>
      <kieli>fi</kieli>
      <asiakastunnus>{self.customer_id}</asiakastunnus>
      <aikaleima>{timestamp}</aikaleima>
      <tarkiste>{signature}</tarkiste>
      <tiketti></tiketti>
    </wmYritysTiedotV3>
  </soap:Body>
</soap:Envelope>"""

        try:
            response = requests.post(self.endpoint, data=body.encode("utf-8"), headers=headers, timeout=20)
            response.raise_for_status()
            return {"raw_xml": response.text}
        except Exception as e:
            return {"error": f"YTJ HTTP error: {e}"}

    def search_companies(self, keyword: str, active_only: bool = True):
        timestamp, signature = self._generate_auth()

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.ytj.fi/wmYritysHaku",
        }

        body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <wmYritysHaku xmlns="http://www.ytj.fi/">
      <hakusana>{keyword}</hakusana>
      <yritysmuoto></yritysmuoto>
      <sanahaku>true</sanahaku>
      <ytunnus></ytunnus>
      <voimassaolevat>{"true" if active_only else "false"}</voimassaolevat>
      <kieli>fi</kieli>
      <asiakastunnus>{self.customer_id}</asiakastunnus>
      <aikaleima>{timestamp}</aikaleima>
      <tarkiste>{signature}</tarkiste>
      <tiketti></tiketti>
    </wmYritysHaku>
  </soap:Body>
</soap:Envelope>"""

        try:
            response = requests.post(self.endpoint, data=body.encode("utf-8"), headers=headers, timeout=20)
            response.raise_for_status()
            return {"raw_xml": response.text}
        except Exception as e:
            return {"error": f"YTJ HTTP error: {e}"}




