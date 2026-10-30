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
    page.title = "FB Multi-Tool"
    page.theme_mode = ft.ThemeMode.LIGHT
    # FIX: ft.Padding (huruf P kapital)
    page.padding = ft.Padding.symmetric(horizontal=20, vertical=30)
    page.scroll = ft.ScrollMode.AUTO

    # Inisialisasi Service Share (Flet 1.0.5)
    share_service = ft.Share()
    
    # Inisialisasi FilePicker (Flet 1.0.5: Sekarang berupa Service)
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    # --- HEADER ---
    header = ft.Column([
        ft.Icon(ft.Icons.SECURITY, size=50, color=ft.Colors.BLUE_700),
        ft.Text("FB Multi-Tool", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Pilih menu dan jalankan program", size=14, color=ft.Colors.GREY_600),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    # --- INPUT UTAMA ---
    cookie_field = ft.TextField(
        label="Cookie", hint_text="Paste cookie (datr=...; c_user=...)",
        multiline=True, min_lines=3, max_lines=5, border_radius=10, text_size=14,
    )
    password_field = ft.TextField(
        label="Password Facebook (Wajib untuk A2f/Ganti Email)", password=True, 
        can_reveal_password=True, border_radius=10, text_size=14,
    )

    # --- DYNAMIC INPUT FIELDS ---
    # Kolom ini hanya muncul jika dicentang menu tertentu
    email_baru_field = ft.TextField(
        label="Masukkan Email Baru", border_radius=10, text_size=14, visible=False
    )
    
    foto_path_text = ft.Text("Belum ada foto dipilih", color=ft.Colors.GREY_600, size=12)
    
    async def pick_foto(e):
        # Flet 1.0.5: FilePicker memakai async/await dan tidak butuh on_result
        files = await file_picker.pick_files(
            dialog_title="Pilih Foto Profil",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png"],
            allow_multiple=False
        )
        if files:
            foto_path_text.value = f"Foto terpilih: {files[0].name}"
            page.update()

    btn_pick_foto = ft.Button(
        "Pilih Foto dari Galeri", icon=ft.Icons.PHOTO_LIBRARY,
        on_click=pick_foto, visible=False, height=40
    )

    # --- CHECKBOX MENU ---
    cb_a2f = ft.Checkbox(label="A2f (Aktifkan 2FA)", value=False)
    cb_foto = ft.Checkbox(label="Set Foto Profil", value=False)
    cb_email = ft.Checkbox(label="Ganti Email", value=False)
    cb_hapus = ft.Checkbox(label="Hapus Email", value=False)

    def on_menu_change(e):
        # Logika Input Dinamis
        email_baru_field.visible = cb_email.value
        btn_pick_foto.visible = cb_foto.value
        foto_path_text.visible = cb_foto.value
        page.update()

    cb_a2f.on_change = on_menu_change
    cb_foto.on_change = on_menu_change
    cb_email.on_change = on_menu_change
    cb_hapus.on_change = on_menu_change

    # --- TOMBOL JALANKAN ---
    btn_run = ft.Button(
        "Mulai Program", icon=ft.Icons.PLAY_ARROW,
        width=float("inf"), height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE,
        )
    )

    # --- LOG & HASIL ---
    log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True, height=200, padding=10)
    log_container = ft.Container(
        content=log_view, bgcolor=ft.Colors.BLACK_87,
        border_radius=10, padding=10, visible=False 
    )

    result_view = ft.Text(selectable=True, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD, size=16)

    # --- FUNGSI SHARE (FIX UNTUK FLET 1.0.5) ---
    async def share_file(e):
        if os.path.exists(RESULT_CSV):
            try:
                # Hapus parameter mime_type, from_path hanya menerima path & name
                file_to_share = ft.ShareFile.from_path(RESULT_CSV, name="hasil_2fa.csv")
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
        # Validasi Input
        if not cookie_field.value:
            log("❌ Cookie tidak boleh kosong!")
            return
        if (cb_a2f.value or cb_email.value) and not password_field.value:
            log("❌ Password wajib diisi untuk menu yang dipilih!")
            return
        if cb_email.value and not email_baru_field.value:
            log("❌ Email baru wajib diisi!")
            return

        btn_run.disabled = True
        btn_run.text = "Memproses..."
        btn_share.visible = False
        log_view.controls.clear()
        result_view.value = ""
        page.update()

        def worker():
            try:
                # LOGIKA PROGRAM DIMULAI DI SINI
                # 1. Jika A2f dicentang, jalankan FBAccountsCenter
                if cb_a2f.value:
                    log("🚀 Menjalankan A2f...")
                    fb = FBAccountsCenter(cookie_field.value, log, on_result)
                    fb.run_all(password_field.value)
                
                # 2. Jika menu lain dicentang, panggil fungsi dari file lain
                # (Kamu tinggal import dan panggil fungsinya di sini nanti)
                if cb_foto.value:
                    log("🚀 Menjalankan Set Foto Profil...")
                    # contoh: ganti_foto.run(cookie_field.value, foto_path_text.value)
                
                if cb_email.value:
                    log("🚀 Menjalankan Ganti Email...")
                    # contoh: ganti_email.run(cookie_field.value, password_field.value, email_baru_field.value)

                if cb_hapus.value:
                    log("🚀 Menjalankan Hapus Email...")
                    # contoh: hapus_email.run(cookie_field.value)

            except Exception as ex:
                log(f"❌ Error Sistem: {ex}")
            finally:
                btn_run.disabled = False
                btn_run.text = "Mulai Program"
                page.update()

        threading.Thread(target=worker, daemon=True).start()

    btn_run.on_click = run_task

    # --- SUSUNAN UI ---
    page.add(
        header, ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        cookie_field, password_field,
        ft.Text("Pilih Menu:", weight=ft.FontWeight.BOLD),
        cb_a2f, cb_foto, cb_email, cb_hapus,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        
        # Input Dinamis
        email_baru_field, btn_pick_foto, foto_path_text,
        
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        btn_run,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Log Proses:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        log_container,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Text("Hasil:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
        result_view, btn_share,
    )

if __name__ == "__main__":
    ft.run(main)
