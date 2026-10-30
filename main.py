import flet as ft
import threading
import os
import csv
import asyncio
from fb_center import FBAccountsCenter

RESULT_CSV = os.path.join(os.path.dirname(__file__), "hasil_2fa.csv")

def simpan_ke_csv(uid, key):
    file_exists = os.path.isfile(RESULT_CSV)
    try:
        with open(RESULT_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["UID", "Key 2FA"])
            writer.writerow([uid, key])
        return True
    except Exception:
        return False

def main(page: ft.Page):
    page.title = "FB 2FA Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    # FIX 1: ft.padding -> ft.Padding
    page.padding = ft.Padding.symmetric(horizontal=20, vertical=30)
    page.scroll = ft.ScrollMode.AUTO

    # Inisialisasi Service Share (Flet 1.0.5)
    share_service = ft.Share()

    header = ft.Column([
        ft.Icon(ft.Icons.SECURITY, size=50, color=ft.Colors.BLUE_700),
        ft.Text("FB 2FA Center", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Otomatisasi aktivasi 2FA Facebook", size=14, color=ft.Colors.GREY_600),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    cookie_field = ft.TextField(
        label="Cookie", hint_text="Paste cookie (datr=...; c_user=...)",
        multiline=True, min_lines=3, max_lines=5, border_radius=10, text_size=14,
    )
    password_field = ft.TextField(
        label="Password Facebook", password=True, can_reveal_password=True,
        border_radius=10, text_size=14,
    )

    btn_run = ft.Button(
        "Mulai Proses", icon=ft.Icons.PLAY_ARROW,
        width=float("inf"), height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE,
        )
    )

    log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True, height=250, padding=10)
    
    # FIX 2: Colors.BLACK87 -> Colors.BLACK_87
    log_container = ft.Container(
        content=log_view, bgcolor=ft.Colors.BLACK_87,
        border_radius=10, padding=10, visible=False 
    )

    result_view = ft.Text(selectable=True, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD, size=16)

    # FIX 3: Fungsi Share yang benar untuk Flet 1.0.5 (Async)
    async def share_file(e):
        if os.path.exists(RESULT_CSV):
            try:
                # Buat objek ShareFile dari path
                file_to_share = ft.ShareFile.from_path(RESULT_CSV, mime_type="text/csv")
                # Panggil service share
                await share_service.share_files([file_to_share], text="Hasil 2FA Facebook")
            except Exception as ex:
                log(f"❌ Gagal share: {ex}")
        else:
            log("❌ Belum ada file yang bisa dibagikan.")
            page.update()

    btn_share = ft.Button(
        "Bagikan File CSV", icon=ft.Icons.SHARE,
        width=float("inf"), height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE,
        ),
        on_click=share_file,
        visible=False 
    )

    def log(msg):
        log_container.visible = True
        # Pastikan log selalu di-update dengan aman
        log_view.controls.append(ft.Text(str(msg), color=ft.Colors.WHITE, size=13, font_family="monospace"))
        page.update()

    def on_result(uid, key):
        result_view.value = f"✅ UID: {uid}\n🔑 Key 2FA: {key}"
        if simpan_ke_csv(uid, key):
            log("✅ Berhasil disimpan ke file CSV internal.")
            btn_share.visible = True 
        else:
            log("❌ Gagal menyimpan ke CSV.")
        page.update()

    def run_task(e):
        btn_run.disabled = True
        btn_run.text = "Memproses..."
        btn_share.visible = False
        log_view.controls.clear()
        result_view.value = ""
        page.update()

        cookie_val = (cookie_field.value or "").strip()
        pwd_val = password_field.value or ""

        if not cookie_val or not pwd_val:
            log("❌ Cookie dan Password tidak boleh kosong!")
            btn_run.disabled = False
            btn_run.text = "Mulai Proses"
            page.update()
            return

        def worker():
            try:
                fb = FBAccountsCenter(cookie_val, log, on_result)
                fb.run_all(pwd_val)
            except Exception as ex:
                log(f"❌ Error Sistem: {ex}")
            finally:
                btn_run.disabled = False
                btn_run.text = "Mulai Proses"
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    btn_run.on_click = run_task

    page.add(
        header, ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        cookie_field, password_field,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        btn_run, ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Log Proses:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        log_container, ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Hasil:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        result_view, btn_share,
    )

if __name__ == "__main__":
    ft.run(main)
