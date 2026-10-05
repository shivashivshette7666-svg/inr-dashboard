"""Daily update: data.json mein aaj ki date ka naya data add karta hai."""
import json, sys, datetime as dt
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

def yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    price = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    return float(price)

def safe(symbol):
    try:
        return yahoo(symbol)
    except Exception as e:
        print(f"WARNING: {symbol} nahi mila: {e}", file=sys.stderr)
        return None

# IST ki aaj ki date
today = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date()
if today.weekday() >= 5:
    print("Weekend hai, kuch add nahi kiya."); sys.exit(0)

data = json.load(open("data.json"))
manual = json.load(open("manual.json"))
d = today.isoformat()
if data["dates"][-1] == d:
    print("Aaj ka data pehle se hai."); sys.exit(0)

S = data["series"]
last = lambda k: next((x for x in reversed(S[k]) if x is not None), None)

usd = safe("USDINR=X")
new = {
    "usd": usd,
    "gbp": safe("GBPINR=X"),
    "eur": safe("EURINR=X"),
    "aed": safe("AEDINR=X"),
    "bse": safe("^BSESN"),
    "nse": safe("^NSEI"),
}
jpy = safe("JPYINR=X");  new["jpy"] = jpy * 100 if jpy else None      # 100 JPY
idr = safe("IDRINR=X");  new["idr"] = idr * 10000 if idr else None    # 10000 IDR

# Gold / Silver: international price (USD/oz) -> INR per 10 g (approx, duty/GST ke bina)
gold, silver = safe("GC=F"), safe("SI=F")
fx = usd or last("usd")
new["gold_24k"] = gold * fx / 31.1035 * 10 if gold else None
new["silver_10g"] = silver * fx / 31.1035 * 10 if silver else None

# Manual rows (manual.json se): iCOMDEX, inflation, GDP, RBI rates
for k, v in manual.items():
    new[k] = v

for k in S:
    v = new.get(k)
    if v is None:
        v = last(k)          # fetch fail hua to pichli value
    S[k].append(round(v, 4) if isinstance(v, float) else v)
data["dates"].append(d)

json.dump(data, open("data.json", "w"))
print("Add hua:", d)
