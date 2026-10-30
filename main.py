import flet as ft
import threading
import os
import csv
from fb_center import FBAccountsCenter

# Path penyimpanan internal aplikasi
RESULT_CSV = os.path.join(os.path.dirname(__file__), "hasil_2fa.csv")

def simpan_ke_csv(uid, key):
    """Menyimpan UID dan Key ke dalam file CSV di dalam sandbox aplikasi"""
    file_exists = os.path.isfile(RESULT_CSV)
    try:
        with open(RESULT_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["UID", "Key 2FA"]) # Header
            writer.writerow([uid, key])
        return True
    except Exception as e:
        print(f"Gagal simpan ke CSV: {e}")
        return False

def main(page: ft.Page):
    page.title = "FB 2FA Center"
    page.theme_mode = ft.ThemeMode.LIGHT
    # Padding responsif untuk layar panjang (1080x2400)
    page.padding = ft.padding.symmetric(horizontal=20, vertical=30)
    page.scroll = ft.ScrollMode.AUTO

    # --- UI ELEMENTS ---
    
    # 1. Header
    header = ft.Column([
        ft.Icon(ft.Icons.SECURITY, size=50, color=ft.Colors.BLUE_700),
        ft.Text("FB 2FA Center", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Otomatisasi aktivasi 2FA Facebook", size=14, color=ft.Colors.GREY_600),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    # 2. Input Fields
    cookie_field = ft.TextField(
        label="Cookie",
        hint_text="Paste cookie dari browser (datr=...; c_user=...)",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_radius=10,
        text_size=14,
    )
    
    password_field = ft.TextField(
        label="Password Facebook",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        text_size=14,
    )

    # 3. Tombol Jalankan
    btn_run = ft.Button(
        "Mulai Proses",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        width=float("inf"), # Full width
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        )
    )

    # 4. Area Log
    log_view = ft.ListView(
        expand=True, 
        spacing=5, 
        auto_scroll=True, 
        height=250, # Tinggi disesuaikan untuk layar panjang
        padding=10
    )
    
    # Container untuk Log agar terlihat seperti terminal/kotak
    log_container = ft.Container(
        content=log_view,
        bgcolor=ft.Colors.BLACK87,
        border_radius=10,
        padding=10,
        visible=False # Sembunyikan dulu sebelum dijalankan
    )

    # 5. Area Hasil & Tombol Share
    result_view = ft.Text(selectable=True, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD, size=16)

    def share_file(e):
        """Fungsi membagikan file CSV ke aplikasi lain (WA, Gmail, dll)"""
        if os.path.exists(RESULT_CSV):
            # Di Flet 1.0.5, kita pakai page.launch_url untuk share atau Share bawaan
            # Kita gunakan URI scheme agar Android membuka menu Share
            import urllib.parse
            # Flet punya fitur Share bawaan yang sangat mudah:
            page.share.share_file(RESULT_CSV, "Bagikan Hasil 2FA")
        else:
            log("❌ Belum ada file yang bisa dibagikan.")
            page.update()

    btn_share = ft.Button(
        "Bagikan File CSV",
        icon=ft.Icons.SHARE,
        width=float("inf"),
        height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
        ),
        on_click=share_file,
        visible=False # Sembunyikan dulu sebelum ada hasil
    )

    # --- LOGIKA APLIKASI ---

    def log(msg):
        log_container.visible = True
        log_view.controls.append(ft.Text(str(msg), color=ft.Colors.WHITE, size=13, font_family="monospace"))
        page.update()

    def on_result(uid, key):
        result_view.value = f"✅ UID: {uid}\n🔑 Key 2FA: {key}"
        if simpan_ke_csv(uid, key):
            log("✅ Berhasil disimpan ke file CSV internal.")
            btn_share.visible = True # Munculkan tombol share
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

    # --- SUSUNAN UI (LAYOUT) ---
    page.add(
        header,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        cookie_field,
        password_field,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        btn_run,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Log Proses:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        log_container,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Hasil:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        result_view,
        btn_share,
    )

if __name__ == "__main__":
    ft.run(main)
