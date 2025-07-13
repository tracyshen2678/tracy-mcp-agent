import hashlib
from datetime import datetime, timedelta


asiakastunnus = "NoCFO"
salainenavain = "E22DAD39-82FA-4930-8274-7FFA057611AD"

# Use Finland local time (UTC+3)
timestamp = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

# Correct sequence: username + secret + timestamp
source = asiakastunnus + salainenavain + timestamp
tarkiste = hashlib.sha1(source.encode("utf-8")).hexdigest().upper()

print("aikaleima:", timestamp)
print("tarkiste:", tarkiste)

