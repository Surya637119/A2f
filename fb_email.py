import requests
import json
import re
from http.cookies import SimpleCookie

class FBAccountsCenterEmail:
    def __init__(self, cookie_string, log_callback):
        self.session = requests.Session()
        self.base_url = "https://accountscenter.facebook.com"
        self.log = log_callback
        self.user_id = None
        self.tokens = {}
        self.fb_dtsg = None
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
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "user-agent": "Mozilla/5.0 (Linux; Android 13; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5896.74 Mobile Safari/537.36",
            "accept": "*/*",
            "x-requested-with": "com.dgd.createfb",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,id-ID;q=0.6,id;q=0.5,fr-FR;q=0.4,fr;q=0.3",
        }

    def _extract_tokens(self, html):
        patterns = {
            'fb_dtsg': r'"token":"(N[^"]+)"',
            'jazoest': r'jazoest=(\d+)',
            '__spin_r': r'"__spin_r":(\d+)',
            '__spin_b': r'"__spin_b":"([^"]+)"',
            '__spin_t': r'"__spin_t":(\d+)',
            'hsi': r'"hsi":"(\d+)"',
            'rev': r'"rev":(\d+)',
        }
        for key, pat in patterns.items():
            m = re.search(pat, html)
            if m: self.tokens[key] = m.group(1)

        hs_m = re.search(r'"haste_session"\s*:\s*"([^"]+)"', html) or re.search(r'"__hs":"([^"]+)"', html)
        if hs_m: self.tokens['__hs'] = hs_m.group(1)
        else: self.tokens.setdefault('__hs', "20517.HYP:accounts_center_pkg.2.1...0")

        self.fb_dtsg = self.tokens.get('fb_dtsg')

    def _parse_json(self, response):
        try:
            return response.json(), None
        except Exception:
            m = re.search(r'({.*})', response.text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1)), None
                except Exception:
                    pass
        return None, f"Gagal parse response: {response.text[:200]}"

    def _step1_get_personal_info(self):
        headers = self.headers.copy()
        headers.update({
            "method": "GET",
            "path": "/personal_info",
            "scheme": "https",
            "dpr": "0.9375",
            "viewport-width": "980",
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "priority": "u=0, i",
        })

        url = f"{self.base_url}/personal_info"
        response = self.session.get(url, headers=headers, allow_redirects=True)

        if 'login.php' in response.url:
            self.log("❌ Redirect ke halaman login — cookies expired atau tidak valid.")
            return None

        self._extract_tokens(response.text)

        if 'fb_dtsg' not in self.tokens:
            self.log("❌ Token fb_dtsg tidak ditemukan. Tidak bisa lanjut.")
            return None

        missing = []
        if 'jazoest' not in self.tokens: missing.append('jazoest')
        if 'rev' not in self.tokens: missing.append('rev')

        if missing:
            self.log(f"⛔ CHECKPOINT — Token tidak lengkap dari response: {', '.join(missing)}")
            return None

        return response

    def _step2_subscriptions(self):
        headers = self.headers.copy()
        headers.update({
            "method": "POST",
            "path": "/api/graphql/",
            "scheme": "https",
            "x-fb-friendly-name": "FXAccountsCenterSubscriptionsRouteResolverQuery",
            "x-asbd-id": "359341",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://accountscenter.facebook.com",
            "referer": "https://accountscenter.facebook.com/personal_info",
            "priority": "u=1, i",
        })

        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "h",
            "__hs": self.tokens.get('__hs'), "dpr": "3", "__ccg": "EXCELLENT",
            "__rev": self.tokens.get('rev'), "__s": "snqt4a:4tws6e:3nwp4b",
            "__hsi": self.tokens.get('hsi', "7613700062851712726"),
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w",
            "__csr": "", "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg'),
            "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'),
            "__spin_b": self.tokens.get('__spin_b', "trunk"), "__spin_t": self.tokens.get('__spin_t'),
            "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXAccountsCenterSubscriptionsRouteResolverQuery",
            "server_timestamps": "true", "variables": '{"id":"SUBSCRIPTIONS"}', "doc_id": "25971034499189586",
        }

        url = f"{self.base_url}/api/graphql/"
        return self.session.post(url, headers=headers, data=data, allow_redirects=True)

    def _step3_add_contact(self, email):
        headers = self.headers.copy()
        headers.update({
            "method": "POST",
            "path": "/api/graphql/",
            "scheme": "https",
            "x-fb-friendly-name": "FXAccountsCenterAddContactPointMutation",
            "x-asbd-id": "359341",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://accountscenter.facebook.com",
            "referer": "https://accountscenter.facebook.com/youraccount/contact_points/?entrypoint=profile_page&is_from_dialog=true",
            "priority": "u=1, i",
        })

        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "12",
            "__hs": self.tokens.get('__hs'), "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": self.tokens.get('rev'), "__s": "jzibkx:yz7v9q:gdljuy",
            "__hsi": self.tokens.get('hsi', "7613655043126933172"),
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w",
            "__csr": "", "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg'),
            "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'),
            "__spin_b": self.tokens.get('__spin_b', "trunk"), "__spin_t": self.tokens.get('__spin_t'),
            "__jssesw": "1", "qpl_active_flow_ids": "241970459",
            "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXAccountsCenterAddContactPointMutation",
            "server_timestamps": "true",
            "variables": json.dumps({
                "country": "US", "contact_point": email, "contact_point_type": "EMAIL",
                "selected_accounts": [self.user_id], "family_device_id": "device_id_fetch_datr",
                "client_mutation_id": f"mutation_id_{self.tokens.get('__spin_t', '1772692264273')}",
            }),
            "doc_id": "24024219683917897", "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]',
        }

        url = f"{self.base_url}/api/graphql/"
        return self.session.post(url, headers=headers, data=data, allow_redirects=True)

    def _step4_confirm_contact(self, email, pin_code):
        headers = self.headers.copy()
        headers.update({
            "method": "POST",
            "path": "/api/graphql/",
            "scheme": "https",
            "x-fb-friendly-name": "FXAccountsCenterContactPointConfirmationDialogVerifyContactPointMutation",
            "x-asbd-id": "359341",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://accountscenter.facebook.com",
            "referer": "https://accountscenter.facebook.com/youraccount/contact_points/?entrypoint=profile_page&is_from_dialog=true",
            "priority": "u=1, i",
        })

        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "18",
            "__hs": self.tokens.get('__hs'), "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": self.tokens.get('rev'), "__s": "jzibkx:yz7v9q:gdljuy",
            "__hsi": self.tokens.get('hsi', "7613655043126933172"),
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow8q0JU",
            "__csr": "", "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg'),
            "jazoest": self.tokens.get('jazoest'), "__spin_r": self.tokens.get('__spin_r'),
            "__spin_b": self.tokens.get('__spin_b', "trunk"), "__spin_t": self.tokens.get('__spin_t'),
            "__jssesw": "1", "qpl_active_flow_ids": "241970459",
            "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "FXAccountsCenterContactPointConfirmationDialogVerifyContactPointMutation",
            "server_timestamps": "true",
            "variables": json.dumps({
                "contact_point": email, "contact_point_type": "EMAIL", "pin_code": pin_code,
                "selected_accounts": [self.user_id], "family_device_id": "device_id_fetch_datr",
                "client_mutation_id": f"mutation_id_{self.tokens.get('__spin_t', '1772692283301')}",
                "contact_point_event_type": "ADD", "normalized_contact_point_to_replace": "",
            }),
            "doc_id": "24829010190041566", "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]',
        }

        url = f"{self.base_url}/api/graphql/"
        return self.session.post(url, headers=headers, data=data, allow_redirects=True)

    def run_ganti_email(self, new_email, pin_code):
        self.log(f"👤 User ID : {self.user_id}")
        
        self.log("⏳ Mengambil token...")
        if not self._step1_get_personal_info():
            return False, "checkpoint"

        self._step2_subscriptions()

        self.log(f"⏳ Menambahkan email {new_email} ...")
        add_resp = self._step3_add_contact(new_email)
        add_json, _ = self._parse_json(add_resp)

        if add_json and 'data' in add_json:
            self.log("✅ Email berhasil ditambahkan!")
        else:
            self.log("⚠️ Gagal menambahkan email.")
            return False, "gagal_tambah"

        self.log("⏳ Mengkonfirmasi PIN...")
        confirm_resp = self._step4_confirm_contact(new_email, pin_code)
        confirm_json, _ = self._parse_json(confirm_resp)

        if confirm_json and 'data' in confirm_json:
            self.log("✅ Konfirmasi berhasil! Email telah diganti.")
            return True, "sukses"
        else:
            self.log("❌ Konfirmasi gagal — PIN salah atau expired.")
            return False, "pin_salah"
