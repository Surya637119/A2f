import requests
import json
import re
from http.cookies import SimpleCookie

class FBAccountsCenterTrigger:
    def __init__(self, cookie_string, log_callback):
        self.session = requests.Session()
        self.base_url = "https://accountscenter.facebook.com"
        self.log = log_callback
        self.user_id = None
        self.tokens = {}
        self._load_cookies(cookie_string)
        self._setup_headers()

    def _load_cookies(self, cookie_string):
        cookie = SimpleCookie()
        cookie.load(cookie_string.strip())
        self.cookies = {k: m.value for k, m in cookie.items()}
        if 'c_user' in self.cookies: self.user_id = self.cookies['c_user']
        else:
            m = re.search(r'c_user=(\d+)', cookie_string)
            if m: self.user_id = m.group(1)
        self.session.cookies.update(self.cookies)
        if not self.user_id: raise ValueError("Cookie tidak valid")

    def _setup_headers(self):
        self.headers = {
            "authority": "accountscenter.facebook.com",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Android WebView";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?1", "sec-ch-ua-platform": '"Android"',
            "user-agent": "Mozilla/5.0 (Linux; Android 13; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5896.74 Mobile Safari/537.36",
            "accept": "*/*", "x-requested-with": "com.dgd.createfb",
        }

    def _extract_tokens(self, html):
        patterns = {'fb_dtsg': r'"token":"(N[^"]+)"', 'jazoest': r'jazoest=(\d+)', '__spin_r': r'"__spin_r":(\d+)', '__spin_b': r'"__spin_b":"([^"]+)"', '__spin_t': r'"__spin_t":(\d+)', 'hsi': r'"hsi":"(\d+)"', 'rev': r'"rev":(\d+)'}
        for k, p in patterns.items():
            m = re.search(p, html)
            if m: self.tokens[k] = m.group(1)
        m = re.search(r'"haste_session"\s*:\s*"([^"]+)"', html)
        if m: self.tokens['__hs'] = m.group(1)
        else: self.tokens.setdefault('__hs', "20517.HYP:accounts_center_pkg.2.1...0")

    def _parse_json(self, response):
        try: return response.json()
        except:
            m = re.search(r'({.*})', response.text, re.DOTALL)
            if m:
                try: return json.loads(m.group(1))
                except: pass
        return None

    def run_trigger(self, new_email):
        self.log(f"👤 User ID: {self.user_id}")
        self.log("⏳ Mengambil token...")
        
        headers = self.headers.copy()
        headers.update({"method": "GET", "path": "/personal_info"})
        resp = self.session.get(f"{self.base_url}/personal_info", headers=headers, allow_redirects=True)
        
        if 'login.php' in resp.url:
            self.log("❌ Cookie expired/checkpoint.")
            return False, "checkpoint"
            
        self._extract_tokens(resp.text)
        if 'fb_dtsg' not in self.tokens or 'jazoest' not in self.tokens:
            self.log("⛔ Akun checkpoint (Token tidak lengkap).")
            return False, "checkpoint"

        # Wajib panggil Subscriptions dulu
        headers.update({"method": "POST", "path": "/api/graphql/", "x-fb-friendly-name": "FXAccountsCenterSubscriptionsRouteResolverQuery"})
        data = {"av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "h", "__hs": self.tokens.get('__hs'), "dpr": "3", "__ccg": "EXCELLENT", "__rev": self.tokens.get('rev'), "__s": "snqt4a:4tws6e:3nwp4b", "__hsi": self.tokens.get('hsi'), "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w", "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg'), "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'), "__spin_b": self.tokens.get('__spin_b', "trunk"), "__spin_t": self.tokens.get('__spin_t'), "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXAccountsCenterSubscriptionsRouteResolverQuery", "variables": '{"id":"SUBSCRIPTIONS"}', "doc_id": "25971034499189586"}
        self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)

        # Tambah Contact (Trigger)
        self.log(f"⏳ Mengirim trigger ke email {new_email}...")
        headers.update({"x-fb-friendly-name": "FXAccountsCenterAddContactPointMutation"})
        data.update({"__req": "12", "__s": "jzibkx:yz7v9q:gdljuy", "fb_api_req_friendly_name": "FXAccountsCenterAddContactPointMutation", "variables": json.dumps({"country": "US", "contact_point": new_email, "contact_point_type": "EMAIL", "selected_accounts": [self.user_id], "family_device_id": "device_id_fetch_datr", "client_mutation_id": f"mutation_id_{self.tokens.get('__spin_t')}"}), "doc_id": "24024219683917897"})
        
        add_resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
        
        if self._parse_json(add_resp):
            self.log("✅ Trigger berhasil! Cek email untuk melihat PIN.")
            return True, "sukses"
            
        self.log("❌ Gagal trigger email.")
        return False, "gagal"
