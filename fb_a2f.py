import requests
import json
import time
from http.cookies import SimpleCookie
import re
import pyotp
from db_manager import simpan_a2f

class FBAccountsCenterA2F:
    def __init__(self, cookie_string, log_callback):
        self.session = requests.Session()
        self.base_url = "https://accountscenter.facebook.com"
        self.log = log_callback
        self.user_id = None
        self.password = None
        self.last_totp_key = None
        self.fb_dtsg = None
        self.tokens = {}
        
        self.static_tokens = {
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow8q0JU",
            "__csr": "giNIQIGnbbb7VcYZXAWi5-B_AZn5BvtJFp6G8B9FAiiWNlqaqLXi-hH8AtbrSKJ9uARjHFQlKmFXJ9Flbloz_V9GiCDVpFkA9GlrAJkqVAd-imVtlGXxe8xOhebyoOaAH_y8CUlz8Kqp1LBKElzUhBy99qy8-5pkqt0BAUSiEG2K8yFUohvolyK8wPxanyGzo663e78jxaUdo-EsUnwFw5iU2Hy4dwEJwMwJwj82QxpfubzeAQEeAfxS13x600nCZ7KfwvC1NwXxmUhUx7g7aA6Hxrw2281ukt0zgiAJDGbwOBxyqq4FprV8mAxK445QF9oCii1UAh8Ki4Gy94i1NH-q4EaHg6qi1jwd95zAqdwfh0SU0iBw1vGii740r-bhoW0-pp8DKuVFF9aQicBAyp4bwDCAzXDyFe9BBAz8CiEnxKiVrxq0cAogaT51C1tg6060O9387Nwey1kz8fpi0MUy8xK8Bzoyi227pEvgcpTwcu1Xw5jw6_gswJABAAypEG9HAGq4ECimbmiQdy4t7g4x4x2VFoa98K1FxaHxSfAAAAh8CjCCJ4BhF8WqmV807zC02okjykcDg0i8BABCDBAVFoK8gyE450k6cg3upUKVU0g4xaqim3i3iimm",
            "__hsdp": "gpqtgnM5-MtgCMUa0d2uoa5G2u0n0HNxA27AwjAAvEywh-PN1NCC6Q-2wmz2P4le6QHBz8ggFyoqg1yUmIgEgwHB5zNgG4T20sUmc78tzAU-q6pOwwDDa2J225gmoy15yEgAJ4c264i7m1owH2EfoG12B3HiigC6OxaswhjxOp550loiCo7e6Up82u48lofN884q1Ng4a3wwp5wSwrpk0cQx90ywLwjE4S2-050Rh81tomwaC3a22A2y2jF2dABw5Bw6TwXwgUb86i0z816o0UO0qBtyVu9GppC9xS2dG1CG1jwMxO2Wq0e1UfE421Wwko2HwBDV2oiAg8QAi5k0MoG3e1eBwuocodU5e6UC7GU30K0T8jwAweK36E5m0FU2zxmi1lw14m4Uy7KA4oS0w84-dAw_w",
            "__hblp": "05fwCw7owyw7qK1eiDAwl8zK5Ev-2ycxa8hu75wio1BV84-16y8G2CnUjwl8-FUK5o887d0wwByESFaAximdwEg4O11wJy9FRwIwjEozVZ0wxO1Iwyg6K8xa68px6Q9UhGU5Sq1fF5Agy1pDwHCCwFHK7ucz8Gi19ypU6p0tEtwgEnwIwlo9E2PDK5opwLUco-9xuE4a6E5a1Hy80xW3i5ES3-EoCwAwmE2VwOwoFawdS0BUmyo4m3O5V8rxq48txW1cxa0gy32681EEGcwKw861cwKwae3O6E5S5UO0dCw7TCgy2C2y1CG2C0Houxe48uCw30olx62m8wJwlEc9o4W2O0w42maAG3Cu0XE12U4uexm5UaErjAxW3a58ekq3-786S1jz98gy8a8C1mxu3S5Ey4Unwn81h8qwlo0Ym5E6y3LF1-0Q87a1Vw",
            "__sjsp": "gpqtgnM5Tr152ZgwMyx8E0Q9VwEm2G0n2vx50xCwjAbDwiE-Q5bgrwmd1Z6wLoC6A09DwpkU2Dg"
        }
        
        self._load_cookies(cookie_string)
        self._setup_headers()

    def _load_cookies(self, cookie_string):
        cookie = SimpleCookie()
        cookie.load(cookie_string.strip())
        self.cookies = {k: m.value for k, m in cookie.items()}
        if 'c_user' in self.cookies:
            self.user_id = self.cookies['c_user']
        else:
            m = re.search(r'c_user=(\d+)', cookie_string)
            if m: self.user_id = m.group(1)
        self.session.cookies.update(self.cookies)
        for name in ('fb_dtsg', 'fb_dtsg_ag'):
            if name in self.cookies:
                self.fb_dtsg = self.cookies[name]
                break
        if not self.user_id:
            raise ValueError("Cookie tidak mengandung c_user")

    def _setup_headers(self):
        self.headers = {
            "authority": "accountscenter.facebook.com",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Android WebView";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "user-agent": "Mozilla/5.0 (Linux; Android 13; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5896.74 Mobile Safari/537.36",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "x-requested-with": "com.dgd.createfb",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,id-ID;q=0.6,id;q=0.5,fr-FR;q=0.4,fr;q=0.3",
        }

    def _extract_tokens(self, response_text):
        self.tokens = {}
        patterns = {
            'fb_dtsg': r'"token":"(N[^"]+)"',
            'jazoest': r'jazoest=(\d+)',
            'rev': r'"rev":(\d+)',
            '__spin_r': r'"__spin_r":(\d+)',
            '__spin_b': r'"__spin_b":"([^"]+)"',
            '__spin_t': r'"__spin_t":(\d+)',
            'hsi': r'"hsi":"(\d+)"',
        }
        for k, p in patterns.items():
            m = re.search(p, response_text)
            if m: self.tokens[k] = m.group(1)
            
        m = re.search(r'"haste_session"\s*:\s*"([^"]+)"', response_text)
        if m: self.tokens['__hs'] = m.group(1)
        
        if 'jazoest' not in self.tokens and 'rev' not in self.tokens:
            return False
            
        defaults = {'jazoest': "25406", 'rev': "1034565359", '__spin_r': "1034565359", '__spin_b': "trunk", '__spin_t': "1772725804", 'hsi': "7613799353589787650", '__hs': "20517.HYP:accounts_center_pkg.2.1...0"}
        for k, v in defaults.items():
            if k not in self.tokens: self.tokens[k] = v
        return True

    def _parse_json(self, response):
        try: return response.json()
        except:
            m = re.search(r'({.*})', response.text, re.DOTALL)
            if m:
                try: return json.loads(m.group(1))
                except: pass
        return None

    def run_a2f(self, password):
        self.password = password
        self.log("⏳ Mengambil data personal...")
        
        # Step 1: Get info
        headers = self.headers.copy()
        headers.update({"method": "GET", "path": "/personal_info"})
        resp = self.session.get(f"{self.base_url}/personal_info", headers=headers, allow_redirects=True)
        
        if not self._extract_tokens(resp.text):
            self.log("❌ Akun checkpoint (Token tidak lengkap).")
            return False, "checkpoint"
            
        if 'login.php' in resp.url:
            self.log("❌ Cookie expired/tidak valid.")
            return False, "checkpoint"
            
        self.log(f"👤 User ID: {self.user_id}")

        # Step 2: Reauth Password
        self.log("⏳ Verifikasi password...")
        timestamp = int(time.time())
        encpass = f"#PWD_BROWSER:0:{timestamp}:{self.password}"
        
        headers.update({"method": "POST", "path": "/api/graphql/", "x-fb-friendly-name": "FXPasswordReauthenticationMutation"})
        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "1s",
            "__hs": self.tokens.get('__hs'), "dpr": "3", "__ccg": "EXCELLENT",
            "__rev": self.tokens.get('rev'), "__s": "4vl9f6:bau96h:1ossit",
            "__hsi": self.tokens.get('hsi'), "__dyn": self.static_tokens['__dyn'],
            "__csr": self.static_tokens['__csr'], "__hsdp": self.static_tokens['__hsdp'],
            "__hblp": self.static_tokens['__hblp'], "__sjsp": self.static_tokens['__sjsp'],
            "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg', ""),
            "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'),
            "__spin_b": self.tokens.get('__spin_b'), "__spin_t": self.tokens.get('__spin_t'),
            "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXPasswordReauthenticationMutation",
            "variables": json.dumps({"input": {"account_id": int(self.user_id), "account_type": "FACEBOOK", "category_name": "SecuredActionInteractWithTwoFactorCategory", "password": {"sensitive_string_value": encpass}, "actor_id": self.user_id, "client_mutation_id": "1"}}),
            "doc_id": "9884242298280664"
        }
        resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
        json_resp = self._parse_json(resp)
        
        reauth_ok = False
        if json_resp and 'data' in json_resp:
            if json_resp['data'].get('xfb_password_reauth_fb_only', {}).get('is_reauth_successful'):
                reauth_ok = True
        elif '"is_reauth_successful":true' in resp.text:
            reauth_ok = True
            
        if not reauth_ok:
            self.log("❌ Password salah atau gagal reauth.")
            return False, "password_salah"

        # Step 3: Generate TOTP
        self.log("⏳ Generate kunci 2FA...")
        headers.update({"x-fb-friendly-name": "useFXSettingsTwoFactorGenerateTOTPKeyMutation"})
        data.update({
            "__req": "25", "dpr": "1", "__s": "mqodem:yz7v9q:gdljuy",
            "fb_api_req_friendly_name": "useFXSettingsTwoFactorGenerateTOTPKeyMutation",
            "variables": json.dumps({"input": {"actor_id": self.user_id, "client_mutation_id": "f14faebc-0d07-43d2-a36b-727ec72a225b", "account_id": self.user_id, "account_type": "FACEBOOK", "device_id": "device_id_fetch_datr", "fdid": "device_id_fetch_datr"}}),
            "doc_id": "9837172312995248"
        })
        resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
        json_resp = self._parse_json(resp)
        
        if json_resp and 'data' in json_resp:
            totp_data = json_resp['data'].get('xfb_two_factor_generate_totp_key', {})
            if 'totp_key' in totp_data:
                self.last_totp_key = totp_data['totp_key']['key_text']
        if not self.last_totp_key:
            self.log("❌ Gagal generate kunci 2FA.")
            return False, "gagal_2fa"

        # Step 4: Enable TOTP
        self.log("⏳ Aktivasi 2FA...")
        verif_code = pyotp.TOTP(self.last_totp_key.replace(" ", "")).now()
        self.log(f"🔢 Kode 2FA: {verif_code}")
        
        headers.update({"x-fb-friendly-name": "useFXSettingsTwoFactorEnableTOTPMutation"})
        data.update({
            "__req": "2b", "__s": "kntcux:yz7v9q:gdljuy",
            "fb_api_req_friendly_name": "useFXSettingsTwoFactorEnableTOTPMutation",
            "variables": json.dumps({"input": {"actor_id": self.user_id, "client_mutation_id": "7111ac58-ab67-4e30-ba41-d7421c4ce04a", "account_id": self.user_id, "account_type": "FACEBOOK", "verification_code": verif_code, "device_id": "device_id_fetch_datr", "fdid": "device_id_fetch_datr"}}),
            "doc_id": "29164158613231327"
        })
        resp = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data)
        json_resp = self._parse_json(resp)
        
        if json_resp and 'data' in json_resp:
            if json_resp['data'].get('xfb_two_factor_enable_totp', {}).get('success'):
                self.log(f"✅ 2FA Berhasil diaktifkan! Key: {self.last_totp_key}")
                simpan_a2f(self.user_id, "", self.last_totp_key) # Simpan ke CSV
                return True, "sukses"
                
        self.log("❌ Gagal mengaktifkan 2FA (kode salah).")
        return False, "gagal_2fa"
