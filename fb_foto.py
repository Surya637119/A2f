import os
import re
import json
import time
import requests

class FacebookProfileUploader:
    STATIC_PARAMS = {
        '__dyn': '7xeUjGU5a5Q1ryaxG4Vp41twWwIxu13wFwhUngS3q2ibwNw9G2Saw8i2S1DwUx60GE3Qwb-q7oc81EEbbwto88422y11wBz83WwgEcEhwGxu782lwv89kbxS1FwnE6a1awhUC7Udo5qfK0zEkxe2GewyDwkUe9obrwh8lwUwOzEjUlDw-wUwxwjFovUuz8e82xxW2-awLyESE7i3C22390bS16xi4UK2K2WEjDxe2B08-269wqQ1fxC13xecwBwWzUlwEKufxamEbbxG1fBG2-1mwto46fwk83KwHwOyUqxG0K8',
        '__csr': 'gb44a2i6PMjhlEt5gV6iMX26xRiGIAIRnqEAyHWEQgIBiOZNa9bEWLBnlkAyfhGhabHRJvlWq9OjaFdoPKpkh6WF-YzRKF6GLiQiFrZ9Rh9q8AVA-uBWKFbAmXSZ2bG8BABGLjJdljJaV7FeRmiVGUzXhd7ybXBRp9pFAAHDQfGh4hK8DpkqiSbDykmWA-aprKuuCVkqcgSKm8GqqBAmcqy9aF2FeQip7KmXyt2SGyeiuVkfAArip5CgR2EWica7aLyFkt7muEym9gvghUJkngHzmWixhkumqbFqCAGdzFrzGCyUWqUdpkqq9KaByUyEDy48m9z8C8Qu9DglHwOAgiAxqfGax94G3KFK5FoW2u269Bg8qxy8zpEozoiyFVUkzUkBy8pwxhFoW5Eqy8S3idy8fES3i5UC1owRDzooxp289Q3W12hbx63uewTwlo5W2O0Fo2MK1nU2VwaB3KbForg9ayAim0gy2m13wrE8eiewi88UW10wVU27xi5EKi3a6Q9w5YwWx90Oy81Y85a598526o9EWElgo82LwcBe3O367z0XK7o4C0LU4e8xm3-4AezE3Tw2SobF8nx604P9E0cAo2uw2l40eSw2uE09jEx08m00yJ806kS1bw7NzoC3uoJ0Fzonw7_wfOaS0kS0-8y0OS660lFwVw25t06Fw2FU0MKayEcodU2y8029W0hadw3q40jm04i818C8yE0PO0pvw6jyIxpQ4U4cUhw9t00hh80kVw6cw2FU2Ew8O4ywoQ0a4wOw1V2EBh6EngqRAAwPo0xYE13E29wKx61ew1RRU3PwKDyp206w8UHyopw',
        '__hsdp': 'gdyh0zexQb68Gag9E9qCCdFA6FE8gAp8fA5Fb1gAy2F28bayA2N1bMOhhF28F1OsAfhQdA1ooO93Xsa88QiSBdG5qOp2GOOWgyp8syHAikCWgDqRkmltN6gxt2Oib8oJlh9rs9yZeaddsy894gyBuSJKOAGH46Ettz44Q9f4yoGOljiyDvhkuygX8as5siSgGHAay5b46b6q9ihfkRGyCZ4jfdmzV1qAbicBjIiGTHhksxe-h2kihc8hCUC59mBqOb64pALmKtJASlknjSW61xHa-zy1gvacCQUxkAXhrK8BQh9z4CmK8NdcwN6yAkPj8p17xabh8AgbVUlp9A4okzESXoOfyEKaXz47EXxq4A4Sye2S9x0x99UHyoC42CiiK8h9UEi5AFUgTgeE8o9HGrBpODDDKmm7qz8KiibzogybyrxS9yoC18wwAUoxV3EjwLCg8E4y10AwKxJ0CzEcoG325EV384e8xm261bzQ2W48nxaawgo663i788UG3qewjHwNDAoPxzS7S0SU-0BotzU768U520CEvDy9okGETzFUK2J6CAxe2mfy88kdwxxO22eUCEljF2UJ1mcwiUfUappobUWVEC8waSh6Cz8G3O2SHXjwSyEycxy9Axm3e3a49UfUV0oEO0xE7W2m3G2e2C4uml28GmfK0FUdosBhEqz8vwgopU8Ubo662uu2a1qwpEnyV81fU6q2C4U660FE98jU1zE7m0IEpwLwGxW220h-1Zwh-0lO3y5U4G4E57wNG1WDU1maw8u3S0DE7iawa60gm3W1CxR0Ew58w8G3u3q6oaogwnE2Fg16o461jz8b8pwIxC685KezUaVE2fwiEdE1jUy2O18gaU1BpUKcwZU7u0n-q0IU563W0FU5y48S13CwHwQw64wajU2bwbq1YwHG',
        '__hblp': '0DLJ0Uh9xjQ3O1Xoc83RiF0Ng14U720FUlzkUG2O1uzUswa24-dU2byUdEd9E5fxq5o2w86U72bg-q5ovwZgS1igWEO3K2i2C2a78dU8V9Udo5u7E2qwHDxG2K10waS6UbEjwTwaOi0LE5p0iUS5o8o4Sdwg8nxa0Fku4Q1HwSzE4W3m7UlwCwbC3e6U2ixd38-1tU3cw-KUy0xVUfo4C2619G2heEObg8EfEO1FwtE2AxK17wMwZwuo-2K7EhwjU6a0iO16wzwFwiE5W1cgjBwmFoeEcUpCxW2S6E4qexy9xS4FE3ewUy82HwlE6q2C4U5C0Goaoig7q10wAyrwSxy1lweG2Wex6cwlofU1Do4vwGw4Nxy7U6a4E57wNG1WDU3ew8CE27wZw9Ci6aye14y8G3uayUlzU8VQ9wNwcC3W19xO7k2y0ky0yEdUdEpwFx21uwioC1lg15rwgo5ecBwCxC2O6oowmUWfyoy69Ey0xEpw5gx90jHy9UO5U4x4AwxGu6U-0R98nwr9UKcCwSU6N2o27wfuEcU23wkofEkw8yVob8aUgzojwLCwHwQwvk2S3i7o6-UgBw9Ru3C2OczoC0JE7O2KE6i',
        '__sjsp': 'gdyh0yOEt2NyayA2q2mFFzqp1Gq2496i3V1qiMk98wYyi2iEF0IlOf9E8AkqgyagsD95Y8j8QdA1gacT3Xsa88QiSAyaEoCAaHbbF29AxOaKh9irF2tGhhplQBbChuc98IxyRiyHKaF3KfdlbAJyosQpe5aGP28989Uhx6h1dkJ0vCgzHB8BBufLoR7gx2ojQ9f8fUd65d5y42Bcxq95udxi4HiNx6q-i4A8gx5x62ym8zS2q7oyA6Eyt4ghg-bP6wOj8p0Cx61ag2vguwl4m188i3V2kU38w6yw0AMwiWx3zEjw_xe027q79kq2u7U1p83Gw',
        '__s': 'nshl77:mv9lgw:uitrpb', '__comet_req': '15', '__ccg': 'EXCELLENT', 'dpr': '1',
    }
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
    ]

    def __init__(self, cookie_string, photo_path, log_callback):
        self.cookie_string = cookie_string
        self.photo_path = photo_path
        self.log = log_callback
        self.session = requests.Session()
        self.uid = None
        self.tokens = {}
        self._parse_cookies()
        
    def _parse_cookies(self):
        for item in self.cookie_string.split('; '):
            if '=' in item:
                k, v = item.split('=', 1)
                self.session.cookies.set(k, v, domain='.facebook.com')
                self.session.cookies.set(k, v, domain='web.facebook.com')
                self.session.cookies.set(k, v, domain='m.facebook.com')
                if k == 'c_user': self.uid = v

    def _extract_tokens_with_regex(self, html):
        tokens = {}
        token_match = re.search(r'"token":"(N[^"]+)"', html)
        if token_match: tokens['fb_dtsg'] = token_match.group(1)
        else:
            dtsg_match = re.search(r'"dtsg":"([^"]+)"', html)
            if dtsg_match: tokens['fb_dtsg'] = dtsg_match.group(1)
        
        jazoest_match = re.search(r'jazoest=(\d+)', html)
        if jazoest_match: tokens['jazoest'] = jazoest_match.group(1)
        
        for pattern in [r'"lsd":"([^"]+)"', r'name="lsd"[^>]+value="([^"]+)"']:
            lsd_match = re.search(pattern, html)
            if lsd_match: 
                tokens['lsd'] = lsd_match.group(1)
                break
        
        rev_match = re.search(r'"rev":(\d+)', html)
        if rev_match: tokens['__rev'] = rev_match.group(1)
        
        hsi_match = re.search(r'"hsi":"(\d+)"', html)
        if hsi_match: tokens['__hsi'] = hsi_match.group(1)
        
        hs_match = re.search(r'"haste_session":"([^"]+)"', html)
        if hs_match: tokens['__hs'] = hs_match.group(1)
        else:
            hs_match2 = re.search(r'"__hs":"([^"]+)"', html)
            if hs_match2: tokens['__hs'] = hs_match2.group(1)
        
        spin_r_match = re.search(r'"__spin_r":(\d+)', html)
        if spin_r_match: tokens['__spin_r'] = spin_r_match.group(1)
        
        spin_t_match = re.search(r'"__spin_t":(\d+)', html)
        if spin_t_match: tokens['__spin_t'] = spin_t_match.group(1)
        
        spin_b_match = re.search(r'"__spin_b":"([^"]+)"', html)
        if spin_b_match: tokens['__spin_b'] = spin_b_match.group(1)
        
        return tokens

    def _get_initial_tokens(self):
        for ua_index, user_agent in enumerate(self.USER_AGENTS, 1):
            self.log(f"    Trying UA #{ua_index}...")
            headers = {
                'authority': 'web.facebook.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
                'sec-ch-ua-mobile': '?1' if 'Android' in user_agent or 'iPhone' in user_agent else '?0',
                'sec-ch-ua-platform': '"Android"' if 'Android' in user_agent else ('"iOS"' if 'iPhone' in user_agent else '"Windows"'),
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'upgrade-insecure-requests': '1',
                'user-agent': user_agent,
            }
            
            try:
                response = self.session.get(f'https://web.facebook.com/profile.php?id={self.uid}', headers=headers, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    html_lower = response.text.lower()
                    if 'logout' in html_lower or 'settings' in html_lower or 'friends' in html_lower:
                        self.log(f"    ✅ Login successful with UA #{ua_index}!")
                        self.tokens = self._extract_tokens_with_regex(response.text)
                        return 'fb_dtsg' in self.tokens
            except Exception as e:
                self.log(f"    ✗ Error: {e}")
        
        return False

    def _upload_photo(self):
        if not os.path.exists(self.photo_path): return None
        boundary = "----WebKitFormBoundary" + "".join([chr(i) for i in range(97, 123)][:16])
        
        with open(self.photo_path, 'rb') as f:
            file_content = f.read()
            
        body_header = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(self.photo_path)}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
        body_footer = f'\r\n--{boundary}--\r\n'.encode()
        
        params = {'photo_source': '57', 'profile_id': self.uid, 'av': self.uid, '__aaid': '0', '__user': self.uid, '__a': '1', '__req': '1n', **self.STATIC_PARAMS}
        params.update({k: v for k, v in self.tokens.items() if k in ['__hs', '__rev', '__hsi', 'fb_dtsg', 'jazoest', 'lsd', '__spin_r', '__spin_t', '__spin_b']})
        
        headers = {
            'authority': 'web.facebook.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://web.facebook.com',
            'referer': f'https://web.facebook.com/profile.php?id={self.uid}',
            'user-agent': self.USER_AGENTS[2], # UA Windows (indeks 2)
            'content-type': f'multipart/form-data; boundary={boundary}',
            'x-asbd-id': '359341',
        }
        if 'lsd' in self.tokens: headers['x-fb-lsd'] = self.tokens['lsd']
        
        resp = self.session.post('https://web.facebook.com/profile/picture/upload/', params=params, data=body_header + file_content + body_footer, headers=headers)
        txt = resp.text[9:] if resp.text.startswith('for (;;);') else resp.text
        try: return json.loads(txt).get('payload', {}).get('fbid')
        except: return None

    def _set_profile_pic(self, fbid):
        variables = {
            "input": {
                "attribution_id_v2": f"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,{int(time.time() * 1000)}000,936964,190055527696468,,", 
                "caption": "", "existing_photo_id": fbid, "expiration_time": None, "profile_id": self.uid, 
                "profile_pic_method": "EXISTING", "profile_pic_source": "TIMELINE", 
                "scaled_crop_rect": {"height": 0.56251, "width": 1, "x": 0, "y": 0.21875}, 
                "skip_cropping": True, "actor_id": self.uid, "client_mutation_id": "1"
            }, 
            "isPage": False, "isProfile": True, "sectionToken": "UNKNOWN", "collectionToken": "UNKNOWN", "scale": 1, 
            "__relay_internal__pv__ProfileGeminiIsCoinFlipEnabledrelayprovider": False
        }
        
        data = {
            'av': self.uid, '__aaid': '0', '__user': self.uid, '__a': '1', '__req': '1o', 'dpr': '1', '__ccg': 'EXCELLENT', 
            '__s': self.STATIC_PARAMS['__s'], '__dyn': self.STATIC_PARAMS['__dyn'], '__csr': self.STATIC_PARAMS['__csr'], 
            '__hsdp': self.STATIC_PARAMS['__hsdp'], '__hblp': self.STATIC_PARAMS['__hblp'], '__sjsp': self.STATIC_PARAMS['__sjsp'], 
            '__comet_req': '15', '__crn': 'comet.fbweb.CometProfileTimelineListViewRoute', 'fb_api_caller_class': 'RelayModern', 
            'fb_api_req_friendly_name': 'ProfileCometProfilePictureSetMutation', 'server_timestamps': 'true', 
            'variables': json.dumps(variables), 'doc_id': '26101621736123633'
        }
        data.update({k: v for k, v in self.tokens.items() if k in ['__hs', '__rev', '__hsi', 'fb_dtsg', 'jazoest', 'lsd', '__spin_r', '__spin_t', '__spin_b']})
        
        headers = {
            'authority': 'web.facebook.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://web.facebook.com',
            'referer': f'https://web.facebook.com/profile.php?id={self.uid}&_rdc=1&_rdr',
            'user-agent': self.USER_AGENTS[2], 
            'x-asbd-id': '359341',
        }
        if 'lsd' in self.tokens: headers['x-fb-lsd'] = self.tokens['lsd']
        
        resp = self.session.post('https://web.facebook.com/api/graphql/', data=data, headers=headers)
        txt = resp.text[9:] if resp.text.startswith('for (;;);') else resp.text
        try:
            return 'profile_picture_set' in json.loads(txt).get('data', {})
        except: return False

    def run_upload(self):
        self.log(f"⏳ Mengambil token Facebook...")
        if not self._get_initial_tokens():
            self.log("❌ Gagal ambil token / Cookie mati.")
            return False, "checkpoint"
            
        self.log(f"⏳ Mengunggah foto: {os.path.basename(self.photo_path)}...")
        fbid = self._upload_photo()
        if not fbid:
            self.log("❌ Gagal upload foto ke server FB.")
            return False, "gagal_foto"
            
        self.log("⏳ Mengeset sebagai foto profil...")
        if self._set_profile_pic(fbid):
            self.log("✅ Foto profil berhasil diganti!")
            return True, "sukses"
            
        self.log("❌ Gagal set foto profil.")
        return False, "gagal_foto"
