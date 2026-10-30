import requests
import json
from http.cookies import SimpleCookie
import re

class FBAccountsCenterDelete:
    def __init__(self, cookie_string, log_callback):
        self.session = requests.Session()
        self.base_url = "https://accountscenter.facebook.com"
        self.log = log_callback
        self.user_id = None
        self.contact_points = []
        self.tokens = {}
        self.target_domain = ""
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
    
    def _setup_headers(self):
        self.headers = {
            "authority": "accountscenter.facebook.com",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Android WebView";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?1", "sec-ch-ua-platform": '"Android"',
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Mi 9T F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.8177.76 Mobile Safari/537.36",
            "content-type": "application/x-www-form-urlencoded", "accept": "*/*",
            "x-requested-with": "com.dgd.createfb",
        }
    
    def _extract_tokens(self, response_text):
        patterns = {'fb_dtsg': r'"token":"(N[^"]+)"', 'jazoest': r'jazoest=(\d+)', '__spin_r': r'"__spin_r":(\d+)', '__spin_b': r'"__spin_b":"([^"]+)"', '__spin_t': r'"__spin_t":(\d+)', 'hsi': r'"hsi":"(\d+)"', 'rev': r'"rev":(\d+)'}
        for k, p in patterns.items():
            m = re.search(p, response_text)
            if m: self.tokens[k] = m.group(1)
        m = re.search(r'"haste_session"\s*:\s*"([^"]+)"', response_text)
        if m: self.tokens['__hs'] = m.group(1)
        else: self.tokens['__hs'] = "20517.HYP:accounts_center_pkg.2.1...0"
    
    def _parse_json(self, response):
        try: return response.json()
        except:
            m = re.search(r'({.*})', response.text, re.DOTALL)
            if m:
                try: return json.loads(m.group(1))
                except: pass
        return None

    def run_delete(self, target_domain):
        self.target_domain = target_domain.strip()
        self.log(f"⏳ Mengambil token...")
        
        headers = self.headers.copy()
        headers.update({"method": "GET", "path": "/personal_info"})
        resp = self.session.get(f"{self.base_url}/personal_info", headers=headers, allow_redirects=True)
        
        if 'login.php' in resp.url:
            self.log("❌ Cookie expired/checkpoint.")
            return False, "checkpoint"
            
        self._extract_tokens(resp.text)
        if 'fb_dtsg' not in self.tokens:
            self.log("❌ Gagal ambil token.")
            return False, "checkpoint"

        # Get Contacts
        self.log("⏳ Mengambil daftar kontak...")
        headers.update({"method": "POST", "path": "/api/graphql/", "x-fb-friendly-name": "FXAccountsCenterContactPointRootQuery"})
        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "v", "__hs": self.tokens.get('__hs'), "dpr": "1", "__ccg": "EXCELLENT", "__rev": self.tokens.get('rev'), "__hsi": self.tokens.get('hsi'), "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w", "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg'), "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'), "__spin_b": self.tokens.get('__spin_b', "trunk"), "__spin_t": self.tokens.get('__spin_t'), "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXAccountsCenterContactPointRootQuery", "variables": "{\"interface\":\"FB_WEB\"}", "doc_id": "24467941749567966"
        }
        resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
        json_resp = self._parse_json(resp)
        
        contact_points_data = []
        if json_resp and 'data' in json_resp and 'fxcal_settings' in json_resp['data']:
            node = json_resp['data']['fxcal_settings'].get('node', {})
            contact_points_data = node.get('all_contact_points', [])

        # Filter
        to_delete = []
        for cp in contact_points_data:
            cp_type = cp.get('contact_point_type', 'UNKNOWN')
            cp_value = cp.get('normalized_contact_point', cp.get('contact_point', 'N/A'))
            if cp_type in ['PHONE_NUMBER', 'PHONE']:
                to_delete.append({'type': cp_type, 'value': cp_value})
            elif cp_type == 'EMAIL' and not cp_value.lower().endswith(f"@{self.target_domain.lower()}"):
                to_delete.append({'type': cp_type, 'value': cp_value})

        if not to_delete:
            self.log(f"✨ Aman! Tidak ada kontak selain domain '@{self.target_domain}'")
            return True, "sukses"

        self.log(f"⚠️ Menemukan {len(to_delete)} kontak yang akan dihapus...")
        
        success_count = 0
        for i, contact in enumerate(to_delete):
            self.log(f"🗑️ ({i+1}/{len(to_delete)}) Hapus: {contact['value']}")
            
            headers.update({"x-fb-friendly-name": "FXAccountsCenterDeleteContactPointMutation"})
            data.update({
                "__req": "15", "__s": "kygbgc:gcrtfd:asum78", "fb_api_req_friendly_name": "FXAccountsCenterDeleteContactPointMutation",
                "variables": json.dumps({"normalized_contact_point": contact['value'], "contact_point_type": contact['type'], "selected_accounts": [self.user_id], "client_mutation_id": f"mutation_id_{self.tokens.get('__spin_t')}", "family_device_id": "device_id_fetch_datr"}), "doc_id": "25195205070065831"
            })
            
            d_resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
            if self._parse_json(d_resp) and 'data' in self._parse_json(d_resp):
                success_count += 1
                self.log(f"   ✅ Berhasil dihapus!")
            else:
                self.log(f"   ❌ Gagal dihapus!")

        self.log(f"📊 Hasil: {success_count} berhasil, {len(to_delete)-success_count} gagal.")
        return True, "sukses"
