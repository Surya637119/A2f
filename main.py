import flet as ft
import threading
import time
import os
import json
from datetime import datetime

# Import semua modul program
from db_manager import (
    get_semua_domain, tambah_domain, simpan_data_email, 
    ambil_dan_hapus_email, get_semua_folder_foto, get_foto_di_folder, FOTO_DIR
)
from menu_upload import tampilkan_menu_upload
from fb_a2f import FBAccountsCenterA2F
from fb_foto import FacebookProfileUploader
from fb_email import FBAccountsCenterEmail
from fb_delete import FBAccountsCenterDelete

# --- STATE GLOBAL UNTUK ANTREAN ---
antrean_tugas = [] # Menyimpan dict tugas
daftar_stop = set() # Menyimpan UID yang di-request stop
worker_aktif = False

def main(page: ft.Page):
    page.title = "FB MultiTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # Inisialisasi Service Android
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    # --- UI KOMPONEN DASAR ---
    def buat_tab(title, content):
        return ft.Tab(text=title, content=ft.Container(content=content, padding=15))

    # ==========================================
    # TAB 1: AUTO SET PROFILE
    # ==========================================
    tb1_cookie = ft.TextField(label="Cookie", multiline=True, min_lines=2, max_lines=4, text_size=12)
    tb1_password = ft.TextField(label="Password FB", password=True, can_reveal_password=True)
    tb1_timer = ft.TextField(label="Timer Mulai (Menit)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    tb1_delay_akun = ft.TextField(label="Jeda Antar Akun (Detik)", value="5", keyboard_type=ft.KeyboardType.NUMBER)
    tb1_delay_prog = ft.TextField(label="Jeda Antar Program (Detik)", value="3", keyboard_type=ft.KeyboardType.NUMBER)

    tb1_cb_a2f = ft.Checkbox(label="A2F", value=False)
    tb1_cb_foto = ft.Checkbox(label="Set Foto Profil", value=False)
    tb1_cb_email = ft.Checkbox(label="Ganti Email", value=False)
    tb1_cb_delete = ft.Checkbox(label="Delete Email", value=False)
    
    # Dropdown Dinamis
    tb1_dd_folder = ft.Dropdown(label="Pilih Folder Foto", visible=False)
    tb1_dd_domain = ft.Dropdown(label="Pilih Domain (Pertahankan)", visible=False)

    def on_cek_program(e):
        tb1_dd_folder.visible = tb1_cb_foto.value
        tb1_dd_domain.visible = tb1_cb_delete.value
        if tb1_cb_foto.value:
            tb1_dd_folder.options = [ft.dropdown.Option(f) for f in get_semua_folder_foto()]
        if tb1_cb_delete.value:
            tb1_dd_domain.options = [ft.dropdown.Option(d) for d in get_semua_domain()]
        page.update()

    tb1_cb_foto.on_change = on_cek_program
    tb1_cb_delete.on_change = on_cek_program

    def mulai_antrean(e):
        cookies = tb1_cookie.value.strip().split('\n') # Bisa multiple cookie pisah enter
        pass_val = tb1_password.value
        
        if not cookies or not cookies[0]:
            page.show_snack_bar(ft.SnackBar(ft.Text("❌ Cookie kosong!")))
            return
            
        program_dipilih = []
        if tb1_cb_a2f.value: program_dipilih.append("A2F")
        if tb1_cb_foto.value: program_dipilih.append("FOTO")
        if tb1_cb_email.value: program_dipilih.append("EMAIL")
        if tb1_cb_delete.value: program_dipilih.append("DELETE")
        
        if not program_dipilih:
            page.show_snack_bar(ft.SnackBar(ft.Text("❌ Pilih minimal 1 program!")))
            return

        try:
            menit = int(tb1_timer.value or 0)
            delay_akun = int(tb1_delay_akun.value or 5)
            delay_prog = int(tb1_delay_prog.value or 3)
        except:
            menit, delay_akun, delay_prog = 0, 5, 3

        waktu_mulai = time.time() + (menit * 60)

        # Masukkan ke antrean
        for c in cookies:
            if c.strip():
                # Ekstrak UID dari cookie
                import re
                uid_match = re.search(r'c_user=(\d+)', c)
                uid = uid_match.group(1) if uid_match else "Unknown"
                
                tugas = {
                    "uid": uid,
                    "cookie": c.strip(),
                    "password": pass_val,
                    "program": program_dipilih,
                    "folder_foto": tb1_dd_folder.value,
                    "domain": tb1_dd_domain.value,
                    "waktu_mulai": waktu_mulai,
                    "delay_akun": delay_akun,
                    "delay_prog": delay_prog,
                    "status": "Waiting"
                }
                antrean_tugas.append(tugas)
                tambah_ke_dashboard(tugas)
        
        page.show_snack_bar(ft.SnackBar(ft.Text(f"✅ {len(cookies)} akun masuk antrean!")))
        tb1_cookie.value = "" # Clear
        page.update()
        
        global worker_aktif
        if not worker_aktif:
            threading.Thread(target=proses_antrean, args=(page,), daemon=True).start()

    tab1_content = ft.Column([
        ft.Text("Pengaturan Akun", weight=ft.FontWeight.BOLD),
        tb1_cookie,
        tb1_password,
        ft.Row([tb1_timer, tb1_delay_akun, tb1_delay_prog]),
        ft.Divider(),
        ft.Text("Pilih Program:", weight=ft.FontWeight.BOLD),
        tb1_cb_a2f, tb1_cb_foto, tb1_cb_email, tb1_cb_delete,
        tb1_dd_folder, tb1_dd_domain,
        ft.Divider(),
        ft.Button("Masukkan ke Antrean", icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, on_click=mulai_antrean)
    ], scroll=ft.ScrollMode.AUTO)

    # ==========================================
    # TAB 2: TRIGGER EMAIL (Placeholder)
    # ==========================================
    tab2_content = ft.Column([
        ft.Text("Fitur Trigger Email Belum Diimplementasikan", color=ft.Colors.GREY)
    ])

    # ==========================================
    # TAB 3: SET DATA EMAIL
    # ==========================================
    tb3_uid = ft.TextField(label="UID")
    tb3_email = ft.TextField(label="Email")
    tb3_pin = ft.TextField(label="Kode Konfirmasi / PIN")

    def simpan_email_klik(e):
        if not tb3_uid.value or not tb3_email.value or not tb3_pin.value:
            page.show_snack_bar(ft.SnackBar(ft.Text("❌ Semua kolom wajib diisi!")))
            return
        simpan_data_email(tb3_uid.value, tb3_email.value, tb3_pin.value)
        page.show_snack_bar(ft.SnackBar(ft.Text("✅ Data email berhasil disimpan!")))
        tb3_uid.value = tb3_email.value = tb3_pin.value = ""
        page.update()

    tab3_content = ft.Column([
        ft.Text("Masukkan Data Email & PIN", weight=ft.FontWeight.BOLD),
        tb3_uid, tb3_email, tb3_pin,
        ft.Button("Simpan ke Database", on_click=simpan_email_klik, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
    ])

    # ==========================================
    # TAB 4: SET DOMAIN
    # ==========================================
    tb4_domain = ft.TextField(label="Domain (Cth: outlook.com)")
    list_domain_view = ft.ListView(expand=True, spacing=5)

    def refresh_domain():
        list_domain_view.controls.clear()
        for d in get_semua_domain():
            list_domain_view.controls.append(ft.Text(f"🌐 {d}"))
        page.update()

    def tambah_domain_klik(e):
        if tb4_domain.value:
            tambah_domain(tb4_domain.value)
            tb4_domain.value = ""
            refresh_domain()

    refresh_domain()
    tab4_content = ft.Column([
        ft.Text("Tambah Domain Target", weight=ft.FontWeight.BOLD),
        ft.Row([tb4_domain, ft.Button("Tambah", on_click=tambah_domain_klik)]),
        ft.Divider(),
        list_domain_view
    ])

    # ==========================================
    # TAB 5: DASHBOARD (Dinamis)
    # ==========================================
    dashboard_list = ft.ListView(expand=True, spacing=10)
    
    tab5_content = ft.Column([
        ft.Text("Status Antrean", weight=ft.FontWeight.BOLD, size=18),
        dashboard_list
    ])

    # ==========================================
    # TAB 6: UPLOAD FOTO
    # ==========================================
    tab6_content = tampilkan_menu_upload(page, file_picker)

    # ==========================================
    # SUSUNAN TAB
    # ==========================================
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Auto Set", content=tab1_content),
            ft.Tab(text="Trigger", content=tab2_content),
            ft.Tab(text="Set Email", content=tab3_content),
            ft.Tab(text="Set Domain", content=tab4_content),
            ft.Tab(text="Dashboard", content=tab5_content),
            ft.Tab(text="Upload Foto", content=tab6_content),
        ],
        expand=1,
    )
    page.add(tabs)

    # ==========================================
    # LOGIKA DASHBOARD & ANTREAN (Worker)
    # ==========================================
    
    def tambah_ke_dashboard(tugas):
        uid = tugas['uid']
        waktu_str = datetime.fromtimestamp(tugas['waktu_mulai']).strftime('%H:%M:%S')
        
        teks_uid = ft.Text(uid, weight=ft.FontWeight.BOLD, size=16)
        teks_status = ft.Text(f"Status: {tugas['status']} (Mulai: {waktu_str})", color=ft.Colors.ORANGE)
        
        def hapus_item(e):
            if tugas in antrean_tugas:
                antrean_tugas.remove(tugas)
            kontainer_item.visible = False
            page.update()

        def stop_item(e):
            daftar_stop.add(uid)
            teks_status.value = "Status: Stopping..."
            page.update()

        kontainer_item = ft.Container(
            content=ft.Column([
                ft.Row([teks_uid, ft.Button("Stop", icon=ft.Icons.STOP, on_click=stop_item, bgcolor=ft.Colors.RED_400), ft.Button("Hapus", icon=ft.Icons.DELETE, on_click=hapus_item)]),
                teks_status
            ]),
            padding=10, border=ft.border.all(1, ft.Colors.GREY), border_radius=8
        )
        
        tugas['_ui_kontainer'] = kontainer_item
        tugas['_ui_status'] = teks_status
        dashboard_list.controls.append(kontainer_item)
        page.update()

    def proses_antrean(page_ref):
        global worker_aktif
        worker_aktif = True
        
        while True:
            tugas_aktif = next((t for t in antrean_tugas if t['status'] == 'Waiting'), None)
            if not tugas_aktif:
                break # Antrean kosong

            uid = tugas_aktif['uid']
            cookie = tugas_aktif['cookie']
            ui_status = tugas_aktif['_ui_status']
            
            # Cek Stop
            if uid in daftar_stop:
                tugas_aktif['status'] = 'Stopped'
                ui_status.value = "Status: Dihentikan User"
                ui_status.color = ft.Colors.GREY
                page_ref.update()
                continue

            # Log Callback (Flet thread-safe)
            def log_ui(msg):
                # Hanya update UI, print ke console untuk debug
                print(f"[{uid}] {msg}")
                # Jika ada log view di UI, bisa diarahkan ke situ

            # Cek Waktu
            waktu_sekarang = time.time()
            if waktu_sekarang < tugas_aktif['waktu_mulai']:
                selisih = int(tugas_aktif['waktu_mulai'] - waktu_sekarang)
                ui_status.value = f"Status: Waiting ({selisih} detik lagi)"
                page_ref.update()
                time.sleep(1)
                continue # Loop lagi

            # --- MULAI PROSES ---
            ui_status.value = "Status: Processing..."
            ui_status.color = ft.Colors.BLUE
            page_ref.update()

            gagal_checkpoint = False
            
            # Eksekusi Berurutan
            for prog in tugas_aktif['program']:
                if uid in daftar_stop:
                    ui_status.value = "Status: Dihentikan User"
                    ui_status.color = ft.Colors.GREY
                    page_ref.update()
                    break
                
                try:
                    if prog == "A2F":
                        app = FBAccountsCenterA2F(cookie, log_ui)
                        ok, status = app.run_a2f(tugas_aktif['password'])
                        if not ok and status == "checkpoint":
                            gagal_checkpoint = True; break
                            
                    elif prog == "FOTO":
                        folder = tugas_aktif['folder_foto']
                        if not folder:
                            continue
                        fotos = get_foto_di_folder(folder)
                        if not fotos:
                            continue # Skip jika kosong
                        # Ambil foto pertama (atau bisa diacak)
                        path_foto = os.path.join(FOTO_DIR, folder, fotos[0])
                        app = FacebookProfileUploader(cookie, path_foto, log_ui)
                        ok, status = app.run_upload()
                        if not ok and status == "checkpoint":
                            gagal_checkpoint = True; break
                            
                    elif prog == "EMAIL":
                        data_email = ambil_dan_hapus_email(uid) # Ambil & Hapus
                        if not data_email:
                            ui_status.value = "Status: Gagal (Data email kosong di DB)"
                            ui_status.color = ft.Colors.RED
                            gagal_checkpoint = True; break # Stop program ini
                            
                        app = FBAccountsCenterEmail(cookie, log_ui)
                        ok, status = app.run_ganti_email(data_email['email'], data_email['pin'])
                        if not ok and status == "checkpoint":
                            gagal_checkpoint = True; break
                            
                    elif prog == "DELETE":
                        domain = tugas_aktif['domain']
                        if not domain: continue
                        app = FBAccountsCenterDelete(cookie, log_ui)
                        ok, status = app.run_delete(domain)
                        if not ok and status == "checkpoint":
                            gagal_checkpoint = True; break
                            
                except Exception as ex:
                    log_ui(f"Error fatal: {ex}")
                    gagal_checkpoint = True
                    break
                
                # Jeda antar program
                time.sleep(tugas_aktif['delay_prog'])

            # Selesai Program
            if gagal_checkpoint:
                tugas_aktif['status'] = 'Gagal'
                ui_status.value = "Status: Gagal / Checkpoint"
                ui_status.color = ft.Colors.RED
            elif uid in daftar_stop:
                tugas_aktif['status'] = 'Stopped'
                ui_status.value = "Status: Dihentikan User"
                ui_status.color = ft.Colors.GREY
            else:
                tugas_aktif['status'] = 'Sukses'
                ui_status.value = "Status: Sukses ✅"
                ui_status.color = ft.Colors.GREEN
                
            page_ref.update()
            
            # Jeda antar akun
            if uid not in daftar_stop:
                time.sleep(tugas_aktif['delay_akun'])
                
            daftar_stop.discard(uid)

        worker_aktif = False

if __name__ == "__main__":
    ft.run(main)
