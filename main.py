import flet as ft
import threading
import json
import os
from fb_center import FBAccountsCenter

COOKIE_CACHE = os.path.join(os.path.dirname(__file__), "cookie_cache.json")
RESULT_FILE = os.path.join(os.path.dirname(__file__), "hasil.json")

def load_cached_cookie():
    if os.path.exists(COOKIE_CACHE):
        try:
            with open(COOKIE_CACHE, "r") as f:
                return json.load(f).get("cookie", "")
        except Exception:
            return ""
    return ""

def save_cookie(cookie_str):
    try:
        with open(COOKIE_CACHE, "w") as f:
            json.dump({"cookie": cookie_str}, f)
    except Exception:
        pass

def append_result(uid, key):
    data = []
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append({"uid": uid, "key": key})
    try:
        with open(RESULT_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def main(page: ft.Page):
    page.title = "FB 2FA Center"
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    cookie_field = ft.TextField(
        label="Cookie",
        multiline=True,
        min_lines=3,
        max_lines=6,
        value=load_cached_cookie(),
        hint_text="Paste cookie dari browser",
    )
    password_field = ft.TextField(
        label="Password Facebook",
        password=True,
        can_reveal_password=True,
    )
    
    # ListView tetap sama di 1.0.5
    log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True, height=260)
    result_view = ft.Text(selectable=True)

    def log(msg):
        log_view.controls.append(ft.Text(str(msg), size=13))
        page.update()

    def on_result(uid, key):
        result_view.value = f"UID: {uid}\nKey 2FA: {key}"
        append_result(uid, key)
        page.update()

    def run_task(e):
        btn.disabled = True
        log_view.controls.clear()
        result_view.value = ""
        page.update()

        cookie_val = (cookie_field.value or "").strip()
        pwd_val = password_field.value or ""

        if not cookie_val:
            log("❌ Cookie kosong")
            btn.disabled = False
            page.update()
            return

        save_cookie(cookie_val)

        def worker():
            try:
                fb = FBAccountsCenter(cookie_val, log, on_result)
                fb.run_all(pwd_val)
            except Exception as ex:
                log(f"❌ Error: {ex}")
            finally:
                btn.disabled = False
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    # 🔥 FIX: ElevatedButton -> Button (Flet 1.0.5)
    btn = ft.Button("Jalankan", on_click=run_task)

    page.add(
        cookie_field,
        password_field,
        btn,
        ft.Text("Log:", weight=ft.FontWeight.BOLD),
        log_view,
        ft.Text("Hasil:", weight=ft.FontWeight.BOLD),
        result_view,
    )

# 🔥 FIX: ft.app(target=main) -> ft.run(main) (Flet 1.0.5)
if __name__ == "__main__":
    ft.run(main)
