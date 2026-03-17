"""
Kite Connect Authentication and Credentials Setup
File: kite_credentials.py
OPTIMIZED: Cached instruments to avoid rate limits
Supports environment variables (VPS) with credentials.json fallback (local dev)
"""

import json
import os
import logging
import requests
import pyotp
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect, KiteTicker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# FILE PATHS
# ============================================
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.txt"

# ============================================
# LOAD CREDENTIALS (env vars first, then file)
# ============================================
def _load_credentials():
    """Load credentials from environment variables or credentials.json"""
    # Priority 1: Environment variables (for VPS / production)
    if os.environ.get("KITE_API_KEY"):
        logger.info("🔑 Loading credentials from environment variables")
        return {
            "API_KEY": os.environ["KITE_API_KEY"],
            "API_SECRET": os.environ["KITE_API_SECRET"],
            "CLIENT_ID": os.environ["KITE_CLIENT_ID"],
            "PASSWORD": os.environ["KITE_PASSWORD"],
            "AUTH_SECRET": os.environ["KITE_AUTH_SECRET"],
        }
    
    # Priority 2: credentials.json (for local development)
    if os.path.exists(CREDENTIALS_FILE):
        logger.info("🔑 Loading credentials from credentials.json")
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    
    raise FileNotFoundError(
        "No credentials found! Set KITE_API_KEY environment variable "
        "or create credentials.json"
    )

creds = _load_credentials()

API_KEY = creds["API_KEY"]
API_SECRET = creds["API_SECRET"]
USER_ID = creds["CLIENT_ID"]
PASSWORD = creds["PASSWORD"]
TOTP_SECRET = creds["AUTH_SECRET"]

kite = KiteConnect(api_key=API_KEY)


# ============================================
# GLOBAL CACHE (IMPORTANT!)
# ============================================
_instruments_cache = None
_instruments_dict = None  # symbol -> instrument mapping

# ============================================
# TOKEN HELPERS
# ============================================
def read_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def write_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

# ============================================
# AUTOMATED LOGIN FLOW
# ============================================
def generate_access_token():
    """Auto-generate access token using credentials + TOTP"""
    logger.info("🔐 Generating new access token...")

    session = requests.Session()
    otp = pyotp.TOTP(TOTP_SECRET).now()

    # Step 1: Login
    r = session.post(
        "https://kite.zerodha.com/api/login",
        data={"user_id": USER_ID, "password": PASSWORD}
    ).json()

    request_id = r["data"]["request_id"]

    # Step 2: 2FA
    session.post(
        "https://kite.zerodha.com/api/twofa",
        data={
            "user_id": USER_ID,
            "request_id": request_id,
            "twofa_value": otp
        }
    )

    # Step 3: Get request_token
    resp = session.get(
        f"https://kite.trade/connect/login?api_key={API_KEY}"
    )

    parsed = urlparse(resp.url)
    query = parse_qs(parsed.query)

    if "request_token" not in query:
        raise RuntimeError(
            "API key not authorized yet. Open this URL once in browser:\n"
            f"{resp.url}"
        )

    request_token = query["request_token"][0]

    # Step 4: Generate access token
    data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]

    kite.set_access_token(access_token)
    write_token(access_token)

    logger.info("✅ Access token generated & saved")
    return access_token

# ============================================
# PUBLIC AUTH FUNCTIONS (USED BY STRATEGIES)
# ============================================
def get_kite_instance():
    """Returns authenticated KiteConnect instance (AUTO)"""
    token = read_token()

    if token:
        kite.set_access_token(token)
        try:
            profile = kite.profile()
            logger.info(f"✓ Connected as: {profile['user_name']}")
            return kite
        except Exception:
            logger.warning("⚠️ Stored token invalid. Re-authenticating...")

    # Token missing or invalid
    generate_access_token()
    profile = kite.profile()
    logger.info(f"✓ Connected as: {profile['user_name']}")
    return kite


def get_kite_ticker():
    """Returns authenticated KiteTicker instance"""
    kite = get_kite_instance()
    kws = KiteTicker(API_KEY, kite.access_token)
    logger.info("✓ KiteTicker created")
    return kws

# ============================================
# OPTIMIZED INSTRUMENT FUNCTIONS (CACHED!)
# ============================================
def load_instruments_cache(force_reload=False):
    """Load and cache all NSE instruments (call once at startup)"""
    global _instruments_cache, _instruments_dict
    
    if _instruments_cache is not None and not force_reload:
        return _instruments_cache
    
    logger.info("📦 Loading NSE instruments (one-time)...")
    kite = get_kite_instance()
    
    try:
        instruments = kite.instruments("NSE")
        _instruments_cache = instruments
        
        # Create fast lookup dictionary
        _instruments_dict = {
            inst["tradingsymbol"]: inst 
            for inst in instruments
        }
        
        logger.info(f"✓ Cached {len(instruments)} NSE instruments")
        return instruments
        
    except Exception as e:
        logger.error(f"Failed to load instruments: {e}")
        return []


def get_nse_equity_symbols(limit=500):
    """Get list of NSE equity symbols (uses cache) - filters out non-standard symbols"""
    import re
    
    instruments = load_instruments_cache()
    
    # Patterns to exclude (substrings)
    exclude_substrings = [
        '-BE', '-ST', '-GB', '-GS',  # BE series, ST series, Gold Bonds, GSec
        'SGB',  # Sovereign Gold Bonds
        '-SM', '-BZ',  # SM, BZ series
        'NIFTY', 'BANKNIFTY',  # Index names
        'IRFC', 'NHAI', 'IREDA', 'REC', 'PFC', 'HUDCO',  # Bond issuers when in bond format
        '-N1', '-N2', '-N3', '-N4', '-N5', '-N6', '-N7', '-N8', '-N9',  # Bond series
        '-NA', '-NB', '-NC', '-ND', '-NE', '-NF', '-NG', '-NH', '-NI', '-NJ',
        '-YI', '-YJ', '-YK', '-YL', '-YM', '-YN',  # More bond series
    ]
    
    # Regex patterns to exclude
    # Matches: starts with 3+ digits (like 850NHAI, 622GS2035)
    bond_pattern = re.compile(r'^\d{3,}')
    # Matches: ends with digit+letter+digit (like 29-N5)
    series_pattern = re.compile(r'\d{2,}-[A-Z]+\d*$')
    
    symbols = []
    for inst in instruments:
        if inst["segment"] == "NSE" and inst["instrument_type"] == "EQ":
            symbol = inst["tradingsymbol"]
            
            # Skip if matches any exclude substring
            if any(pattern in symbol for pattern in exclude_substrings):
                continue
            
            # Skip if starts with 3+ digits (bonds like 850NHAI)
            if bond_pattern.match(symbol):
                continue
                
            # Skip if matches bond series pattern (like xxx29-N5)
            if series_pattern.search(symbol):
                continue
            
            symbols.append(symbol)
    
    logger.info(f"Found {len(symbols)} pure equity symbols (filtered)")
    return symbols[:limit]


def get_instrument_token(symbol, exchange="NSE"):
    """Get instrument token for a symbol (uses cache)"""
    global _instruments_dict
    
    # Load cache if not loaded
    if _instruments_dict is None:
        load_instruments_cache()
    
    # Fast dictionary lookup
    instrument = _instruments_dict.get(symbol)
    
    if instrument and instrument["exchange"] == exchange:
        return instrument["instrument_token"]
    
    # Fallback: search in list
    instruments = load_instruments_cache()
    instrument = next(
        (inst for inst in instruments 
         if inst["tradingsymbol"] == symbol and inst["exchange"] == exchange),
        None
    )
    
    if instrument:
        return instrument["instrument_token"]
    
    logger.warning(f"Instrument not found: {symbol}")
    return None


def get_instruments_batch(symbols, exchange="NSE"):
    """Get multiple instrument tokens at once (efficient)"""
    global _instruments_dict
    
    # Load cache if not loaded
    if _instruments_dict is None:
        load_instruments_cache()
    
    result = {}
    for symbol in symbols:
        instrument = _instruments_dict.get(symbol)
        if instrument and instrument["exchange"] == exchange:
            result[symbol] = instrument["instrument_token"]
    
    return result


def test_connection():
    print("\n" + "=" * 70)
    print("Testing Kite Connect...")
    print("=" * 70)

    kite = get_kite_instance()

    try:
        profile = kite.profile()
        print(f"\n✓ User: {profile['user_name']} ({profile['email']})")

        margins = kite.margins()
        print(f"✓ Equity: ₹{margins['equity']['available']['live_balance']:,.2f}")

        quote = kite.quote("NSE:RELIANCE")
        ltp = quote["NSE:RELIANCE"]["last_price"]
        print(f"✓ RELIANCE LTP: ₹{ltp}")

        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


# ============================================
# CLI (OPTIONAL)
# ============================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("KITE CONNECT AUTHENTICATION (AUTOMATED)")
    print("=" * 70)
    print("\n1. Test connection")
    print("2. Load instruments cache")
    print("3. Exit")

    choice = input("\nChoice (1-3): ").strip()

    if choice == "1":
        test_connection()
    elif choice == "2":
        load_instruments_cache()
        print(f"\n✓ Loaded {len(_instruments_cache)} instruments")
    else:
        print("\nGoodbye!")