import requests
import json
import re
from http.cookies import SimpleCookie

class FBAccountsCenterDelete:
    def __init__(self, cookie_string, log_callback):
        self.session = requests.Session()
        self.base_url = "https://accountscenter.facebook.com"
        self.log = log_callback
        self.user_id = None
        self.contact_points = []
        self.fb_dtsg = None
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
        # Header disamakan persis dengan delete_otomatis.py
        self.headers = {
            "authority": "accountscenter.facebook.com",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Android WebView";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Mi 9T F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.8177.76 Mobile Safari/537.36",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "x-requested-with": "com.dgd.createfb",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7,id-ID;q=0.6,id;q=0.5,fr-FR;q=0.4,fr;q=0.3",
        }
    
    def _extract_all_tokens(self, response_text):
        # Disamakan persis dengan delete_otomatis.py
        token_pattern = r'"token":"(N[^"]+)"'
        token_match = re.search(token_pattern, response_text)
        if token_match:
            self.tokens['fb_dtsg'] = token_match.group(1)
            self.fb_dtsg = self.tokens['fb_dtsg']
        
        jazoest_pattern = r'jazoest=(\d+)'
        jazoest_match = re.search(jazoest_pattern, response_text)
        if jazoest_match:
            self.tokens['jazoest'] = jazoest_match.group(1)
        
        spin_r_pattern = r'"__spin_r":(\d+)'
        spin_r_match = re.search(spin_r_pattern, response_text)
        if spin_r_match:
            self.tokens['__spin_r'] = spin_r_match.group(1)
        
        spin_b_pattern = r'"__spin_b":"([^"]+)"'
        spin_b_match = re.search(spin_b_pattern, response_text)
        if spin_b_match:
            self.tokens['__spin_b'] = spin_b_match.group(1)
        
        spin_t_pattern = r'"__spin_t":(\d+)'
        spin_t_match = re.search(spin_t_pattern, response_text)
        if spin_t_match:
            self.tokens['__spin_t'] = spin_t_match.group(1)
        
        hsi_pattern = r'"hsi":"(\d+)"'
        hsi_match = re.search(hsi_pattern, response_text)
        if hsi_match:
            self.tokens['hsi'] = hsi_match.group(1)
        
        rev_pattern = r'"rev":(\d+)'
        rev_match = re.search(rev_pattern, response_text)
        if rev_match:
            self.tokens['rev'] = rev_match.group(1)
        
        hs_pattern = r'"haste_session"\s*:\s*"([^"]+)"'
        hs_match = re.search(hs_pattern, response_text)
        if hs_match:
            self.tokens['__hs'] = hs_match.group(1)
            self.tokens['haste_session'] = hs_match.group(1)
        else:
            hs_pattern2 = r'"__hs":"([^"]+)"'
            hs_match2 = re.search(hs_pattern2, response_text)
            if hs_match2:
                self.tokens['__hs'] = hs_match2.group(1)
            else:
                self.tokens['__hs'] = "20517.HYP:accounts_center_pkg.2.1...0"
        
        return self.tokens
    
    def _parse_json(self, response):
        try:
            return response.json()
        except:
            json_match = re.search(r'({.*})', response.text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            return None

    def _get_personal_info(self):
        self.log("\n📌 STEP 1: Mengambil Token")
        
        headers = self.headers.copy()
        headers.update({
            "method": "GET",
            "path": "/personal_info",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "upgrade-insecure-requests": "1",
            "viewport-width": "980",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
        })
        
        url = f"{self.base_url}/personal_info"
        response = self.session.get(url, headers=headers, allow_redirects=True)
        
        if 'login.php' in response.url:
            self.log("\n❌ ERROR: Redirect ke halaman login! Cookies expired atau tidak valid.")
            return None
        
        self._extract_all_tokens(response.text)
        return response

    def _graphql_contact_point_root(self):
        self.log("\n📌 STEP 2: Mengambil Data Kontak")
        
        if not self.user_id or 'fb_dtsg' not in self.tokens:
            self.log("❌ User ID atau Token fb_dtsg tidak ditemukan!")
            return None
        
        headers = self.headers.copy()
        headers.update({
            "method": "POST",
            "path": "/api/graphql/",
            "scheme": "https",
            "x-fb-friendly-name": "FXAccountsCenterContactPointRootQuery",
            "x-asbd-id": "359341",
            "origin": "https://accountscenter.facebook.com",
            "referer": "https://accountscenter.facebook.com/profiles",
            "priority": "u=1, i"
        })
        
        # Payload disamakan persis dengan delete_otomatis.py
        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "v",
            "__hs": self.tokens.get('__hs', "20517.HYP:accounts_center_pkg.2.1...0"),
            "dpr": "1", "__ccg": "EXCELLENT", "__rev": self.tokens.get('rev', "1034549618"),
            "__hsi": self.tokens.get('hsi', "7613664175148709899"),
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w",
            "__csr": "gjNATn9kARj4kI9nR-iyQKAx3pZd9veLnF4-izqh4sITmAGh3kW8UFqF4AHIyjihqcngABqAJ2RBWRDGHBFlleBQF8C4klaLauGUDJ2UyqbxKqQVta8gxrAuYyAAVVXwDwzyF8ybwwzEozrABzGzogVBxe-axyQm794awNx67SmZ4BiyoaBgsxCmpaVE2iyo3IAxi1Rw-wXK0QGwCg5W3W8wiaakB0AoFKcxq9wl89U-2q1Vw05W5hXBw8Bwsoe8mF16ahQ1Rh8lBxnw21U1soC8gqy5ypF94aw-wwAxDK498Oiiax2t7zCu8zFp8cE52ip1pd5BAwsLWBxSagjwqXwMweyul1h1m0YQ3t1e02EGii740la1zDxaeU3OKayXGiVkqiimiUymiVpUkxOqi9ByX8UiKaz8Cim2SF998qw38S43dh8qwnk1w1wEC9387Nwey1dDwBxqECpwOyoyi7VoyidwwxSq7EcExk0wo0xu0r-l163uimiiidWhFoCi6Q8zeqHgjy4t0Sx53FFHwPACwqogAKcK7bh8GiiiqqqQmh6ACCDyp8",
            "__hsdp": "gpqlgoiI1VMEMQa0d5CC2FEmwxw5x9j5Cg8Vo4-VQCi19k-Z6FNaudyqwGeycMEEnxHGZ0Yxy0pz41gm7A24kic445ob8lc2-2S5O0vOx7gkwSAxNesMnzkagcUrwU2EbonwH3xRgy38Edi3k7l40oo887u1foW3t99Q1GwjAezxm1wwz809Dg1wrwr-cw3do0Vu1zzqwbW6Vk1eJ8-q0gqiq02zaq09fxi789o1v981x415G6o2WwgU2dwWwIwgo6O3OpwcSVorwCx6bwjE6K2uEpzE7e2Wq7E4G1dwk81586y2u2e5E6a680yS0bHwdaE5W0SE1K8Kfw",
            "__hblp": "04cwqo1S88o1SXwjQVES1aDGaz-EW3-m48-68W9wQwBw6mwSw_wygqx6uqm1wGawZwnUy5FUbF88627Ugy84W1Ex51rx-1kxq3C0D8ixO1EwwG2K4d1212wkrUbpki8x65o5y5EsUK8jK6EjU4O79bwJwjU5e1Wx62y581584uibzUyczUlwYxa5EjwRzo0xy687G3q2Py85m2N0no4C1jw8C0G866cwJwoVFGyo2QwtoiyopzEsw9a2e3S2a6UbE1580aorw8e0Fo30wno4Xw8edxu2afwk8jwyxy6ohw82axW11wIxG6EaEK322F0k84e49USawzCx22S0B8rUnxadyEgxC2y0AWxCewaa7U8U4a19yUcE6idwj82ywgEO6UhwoE1Wokw3cU2XxCUcE5u0ne0XU9o",
            "__sjsp": "gprR1xaM9A2p0IT23j68UEe2a0bTCC2Etwxw5Cgkg7CcwvQ6o6C7U",
            "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg', ""),
            "jazoest": self.tokens.get('jazoest', "25423"),
            "__spin_r": self.tokens.get('__spin_r', "1034549618"),
            "__spin_b": self.tokens.get('__spin_b', "trunk"),
            "__spin_t": self.tokens.get('__spin_t', "1772694330"),
            "__jssesw": "1", "qpl_active_flow_ids": "241970459",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "FXAccountsCenterContactPointRootQuery",
            "server_timestamps": "true", "variables": "{\"interface\":\"FB_WEB\"}",
            "doc_id": "24467941749567966", "fb_api_analytics_tags": "[\"qpl_active_flow_ids=241970459\"]"
        }
        
        response = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data, allow_redirects=True)
        json_resp = self._parse_json(response)
        
        if json_resp:
            try:
                self.contact_points = []
                contact_points_data = []
                if 'data' in json_resp and 'fxcal_settings' in json_resp['data']:
                    node = json_resp['data']['fxcal_settings'].get('node', {})
                    contact_points_data = node.get('all_contact_points', [])
                
                if contact_points_data:
                    for i, cp in enumerate(contact_points_data, 1):
                        cp_type = cp.get('contact_point_type', 'UNKNOWN')
                        cp_value = cp.get('normalized_contact_point', cp.get('contact_point', 'N/A'))
                        pending = cp.get('has_any_pending_status', cp.get('is_pending', False))
                        status = "⏳ Pending" if pending else "✅ Terverifikasi"
                        
                        self.contact_points.append({'index': i, 'type': cp_type, 'value': cp_value, 'pending': pending})
                        self.log(f"  [{i}] {cp_type}: {cp_value} ({status})")
                    
                    self.log(f"✅ Total: {len(self.contact_points)} kontak ditemukan.")
                else:
                    self.log("❌ Tidak menemukan data contact points dalam response.")
            except Exception as e:
                self.log(f"❌ Error parsing contacts: {e}")
        else:
            self.log("⚠️ Gagal parse JSON dari kontak.")
        
        return response

    def _graphql_delete_contact(self, contact_info):
        contact_value = contact_info['value']
        contact_type = contact_info['type']
        
        self.log(f"🗑️ Menghapus: {contact_value} ({contact_type})")
        
        headers = self.headers.copy()
        headers.update({
            "method": "POST", "path": "/api/graphql/", "scheme": "https",
            "x-fb-friendly-name": "FXAccountsCenterDeleteContactPointMutation",
            "x-asbd-id": "359341", "origin": "https://accountscenter.facebook.com",
            "referer": "https://accountscenter.facebook.com/youraccount/contact_points/?entrypoint=profile_page&is_from_dialog=true",
            "priority": "u=1, i"
        })
        
        # Payload disamakan persis dengan delete_otomatis.py
        data = {
            "av": self.user_id, "__user": self.user_id, "__a": "1", "__req": "15",
            "__hs": self.tokens.get('__hs', "20517.HYP:accounts_center_pkg.2.1...0"),
            "dpr": "1", "__ccg": "EXCELLENT", "__rev": self.tokens.get('rev', "1034549618"),
            "__s": "kygbgc:gcrtfd:asum78", "__hsi": self.tokens.get('hsi', "7613664175148709899"),
            "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zE2ZwrUdUcobU3Cwr86C1nwro2PxW1ow4-w",
            "__csr": "gjNATn9kARj4kI9nR-iyQKAx3pZd9veLnF4-izqiQsITmAGmzkW8UFqF4AHIyjihqcn8sBqAJ2RheJpWGVqlljTQF8C4kZaLauGUDJ2UyqbxKqQVta8gxrAuYyAAVVXwDwzyF8ybwwzEozrABzGzogVBxe-axyQmi5V4awNx67TKZ4BiyoaBgsxCmpaVE2iyo3IAxi1Rw-wXK0QGwCg5W3W8wiaakB0AoFKcxq9wl89U-2q1Vw05W5hXBw8Bwsoe8mF16ahQ1Rh8lBxnw21U1soC8gqy5ypF94aw-wwAxDK498Oiiax2t7zCu8zFp8cE52ip1pd5BAwsLWBxSagjwqXwMweyul1h1m0YQ3t1e02EGii740la1zDxaeU3OKayXGiVkqiimiUymiVpUkxOqi9ByX8UiKaz8Cim2SF998qw38S43dh8qwnk1w1wEC9387Nwey1dDwBxqECpwOyoyi7VoyidwwxSq7EcExk0wo0xu0r-l163uimiiidWhFoCi6Q8zeqHgjy4t0Sx53FFHwPACwqogAKcK7bh8GiiiqqqQmh6ACCDyp8",
            "__hsdp": "gpqlgoiI1VMEMQa0d5CC2FEmwxw5x9j5Cgmz9o4Vet9Ag4xjXQr94FUS9G2EW8P2yyoS6KLQ3mq6aw6lN0k5xV0w5Az111m2O5j0LwJxsw7YEhQ58dF8sjDc5UR2A3e6Ue0G2S5UaMUtk8wOa3kwR1Rh066221TwjSewTiit0qE4V3EUlwo88O02pQ0o6U6_z80Pm0enwoUSE2-xKl0jHifCw46ACw0EOCw2jUkxO2m0nOi0oh0hqxC0KE4e0zoeEb8461IwYCo3dKm6U9EhyU4W1HwDG6oW1PwKCxW1awjo520hi1EwDwzxq1yxy08Jw2WU3iG1uwdG0rybzU",
            "__hblp": "04cwqo1S88o1SXwjQVES1aDGaz-EW3-m48-68W9wQwBw6mwSw_wygqx6uqm1wGawZwnUy5FUbF886fx7Ugy84W1EByQ5K7U5i5EvxC0D8ixO1EwwG2K4d1212wkrUbpki8x65o5y5EsUK8jK6EjU4O79bwJwjU5e1Wx62y581584uibzUyczUlwYxa5EjwRzo0xy687G3q2Py85m2N0no4C1jw8C0G866cwJwoVFGyo2NG1Rxa9xCexO0AE8Ufo8ErwKw4kw0FxK0wU2Bwc21twjK0wUS5U8E-1gxe2a68px60w8G7E462O6EqwGyUc8aA1gwgUgDzoG2eq48bo2kxLxu4ESax26oa82jG6oW0EEvwzwgE4CbwOwp8S1cwaa12z8rx61yw7Fxi0cPwbK6rwOwlU1sU3LwBw",
            "__sjsp": "gpqlgoiI2p0CgbdMwMyzyw3hpFwG7o8o1pA545E6538G1zx11C1rzovUeE8E1_E",
            "__comet_req": "5", "fb_dtsg": self.tokens.get('fb_dtsg', ""),
            "jazoest": self.tokens.get('jazoest', "25423"),
            "__spin_r": self.tokens.get('__spin_r', "1034549618"),
            "__spin_b": self.tokens.get('__spin_b', "trunk"),
            "__spin_t": self.tokens.get('__spin_t', "1772694330"),
            "__jssesw": "1", "qpl_active_flow_ids": "241970459",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "FXAccountsCenterDeleteContactPointMutation",
            "server_timestamps": "true",
            "variables": json.dumps({
                "normalized_contact_point": contact_value,
                "contact_point_type": contact_type,
                "selected_accounts": [self.user_id],
                "client_mutation_id": f"mutation_id_{self.tokens.get('__spin_t', '1772694598930')}",
                "family_device_id": "device_id_fetch_datr"
            }),
            "doc_id": "25195205070065831",
            "fb_api_analytics_tags": "[\"qpl_active_flow_ids=241970459\"]"
        }
        
        response = self.session.post(f"{self.base_url}/api/graphql/", headers=headers, data=data, allow_redirects=True)
        json_response = self._parse_json(response)
        return json_response and 'data' in json_response

    def run_delete(self, target_domain):
        self.target_domain = target_domain.strip().lower()
        self.log(f"👤 User ID: {self.user_id}")
        self.log(f"🌐 Target Domain: @{self.target_domain}")
        
        get_response = self._get_personal_info()
        if not get_response or 'fb_dtsg' not in self.tokens:
            self.log("❌ Gagal mendapatkan token. Program berhenti.")
            return False, "checkpoint"
        
        self._graphql_contact_point_root()
        
        # Filter otomatis
        to_delete = []
        for cp in self.contact_points:
            val = cp['value'].lower()
            if cp['type'] in ['PHONE_NUMBER', 'PHONE']:
                to_delete.append(cp)
            elif cp['type'] == 'EMAIL':
                if not val.endswith(f"@{self.target_domain}"):
                    to_delete.append(cp)
        
        if not to_delete:
            self.log(f"\n✨ Aman! Tidak ada kontak selain domain '@{self.target_domain}'")
            return True, "sukses"
            
        self.log(f"\n⚠️ Menemukan {len(to_delete)} kontak yang akan dihapus...")
        
        success_count = 0
        fail_count = 0
        
        for i, contact in enumerate(to_delete, 1):
            self.log(f"\n🔄 Progress: {i}/{len(to_delete)}")
            if self._graphql_delete_contact(contact):
                success_count += 1
                self.log("   ✅ Berhasil dihapus!")
            else:
                fail_count += 1
                self.log("   ❌ Gagal dihapus!")
                
        self.log(f"\n📊 HASIL EKSEKUSI: {success_count} Berhasil, {fail_count} Gagal")
        return True, "sukses"
