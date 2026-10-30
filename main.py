import flet as ft
import threading
import time
import os
import re
import random
from datetime import datetime

# Import semua modul program
from db_manager import (
    get_semua_domain, tambah_domain, simpan_data_email, 
    ambil_dan_hapus_email, get_semua_folder_foto, get_foto_di_folder, get_path_foto
)
from fb_a2f import FBAccountsCenterA2F
from fb_foto import FacebookProfileUploader
from fb_email import FBAccountsCenterEmail
from fb_delete import FBAccountsCenterDelete
from fb_trigger import FBAccountsCenterTrigger

# --- STATE GLOBAL ---
antrean_tugas = []
daftar_stop = set()

async def _update_ui(control, **kwargs):
    for k, v in kwargs.items():
        setattr(control, k, v)
    control.update()

def buat_kotak_log(height=180):
    lv = ft.ListView(expand=True, spacing=5, auto_scroll=True, height=height, padding=10)
    container = ft.Container(content=lv, bgcolor=ft.Colors.BLACK_87, border_radius=10, padding=10, visible=False)
    return lv, container

def main(page: ft.Page):
    page.title = "FB MultiTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15 
    
    def show_msg_dialog(msg):
        page.show_dialog(ft.SnackBar(ft.Text(msg)))

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
    
    tb1_dd_folder = ft.Dropdown(label="Pilih Folder Foto", visible=False)
    tb1_dd_domain = ft.Dropdown(label="Pilih Domain (Pertahankan)", visible=False)
    tb1_log_lv, tb1_log_ctn = buat_kotak_log(height=200)

    def log_tb1(msg):
        tb1_log_ctn.visible = True
        tb1_log_lv.controls.append(ft.Text(str(msg), color=ft.Colors.WHITE, size=12, font_family="monospace"))
        page.update()

    def on_cek_program(e):
        tb1_dd_folder.visible = tb1_cb_foto.value
        tb1_dd_domain.visible = tb1_cb_delete.value
        if tb1_cb_foto.value: tb1_dd_folder.options = [ft.DropdownOption(f) for f in get_semua_folder_foto()]
        if tb1_cb_delete.value: tb1_dd_domain.options = [ft.DropdownOption(d) for d in get_semua_domain()]
        page.update()

    tb1_cb_foto.on_change = on_cek_program
    tb1_cb_delete.on_change = on_cek_program

    def mulai_antrean(e):
        cookies = tb1_cookie.value.strip().split('\n')
        if not cookies or not cookies[0]:
            show_msg_dialog("❌ Cookie kosong!"); return
            
        progs = []
        if tb1_cb_a2f.value: progs.append("A2F")
        if tb1_cb_foto.value: progs.append("FOTO")
        if tb1_cb_email.value: progs.append("EMAIL")
        if tb1_cb_delete.value: progs.append("DELETE")
        if not progs: show_msg_dialog("❌ Pilih minimal 1 program!"); return

        try: menit, d_akun, d_prog = int(tb1_timer.value), int(tb1_delay_akun.value), int(tb1_delay_prog.value)
        except: menit, d_akun, d_prog = 0, 5, 3

        waktu_mulai = time.time() + (menit * 60)
        count = 0

        for c in cookies:
            if c.strip():
                uid_match = re.search(r'c_user=(\d+)', c)
                uid = uid_match.group(1) if uid_match else "Unknown"
                
                tugas = {
                    "uid": uid, "cookie": c.strip(), "password": tb1_password.value,
                    "program": progs, "folder_foto": tb1_dd_folder.value,
                    "domain": tb1_dd_domain.value, "waktu_mulai": waktu_mulai,
                    "delay_akun": d_akun, "delay_prog": d_prog, "status": "Waiting"
                }
                antrean_tugas.append(tugas)
                
                # Buat UI untuk akun ini & jalankan thread-nya sendiri
                ui_status, ui_kontainer = tambah_ke_dashboard(tugas)
                tugas['_ui_status'] = ui_status
                tugas['_ui_kontainer'] = ui_kontainer
                
                threading.Thread(target=jalankan_tugas, args=(tugas, page), daemon=True).start()
                count += 1
        
        show_msg_dialog(f"✅ {count} akun dimasukkan ke antrean!")
        tb1_cookie.value = ""
        page.update()

    tab1_content = ft.Column([
        ft.Text("Pengaturan Akun", weight=ft.FontWeight.BOLD),
        tb1_cookie, tb1_password, tb1_timer, tb1_delay_akun, tb1_delay_prog,
        ft.Divider(),
        ft.Text("Pilih Program:", weight=ft.FontWeight.BOLD),
        tb1_cb_a2f, tb1_cb_foto, tb1_cb_email, tb1_cb_delete,
        tb1_dd_folder, tb1_dd_domain,
        ft.Divider(),
        ft.Button(content=ft.Text("Masukkan ke Antrean"), icon=ft.Icons.PLAY_ARROW, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, on_click=mulai_antrean),
        ft.Divider(),
        ft.Text("Log Proses:", weight=ft.FontWeight.BOLD),
        tb1_log_ctn
    ], scroll=ft.ScrollMode.AUTO)

    # ==========================================
    # TAB 2: TRIGGER EMAIL
    # ==========================================
    tb2_cookie = ft.TextField(label="Cookie", multiline=True, min_lines=2, max_lines=4, text_size=12)
    tb2_email = ft.TextField(label="Email Target (Yang mau di-trigger)")
    tb2_log_lv, tb2_log_ctn = buat_kotak_log(height=200)

    def log_tb2(msg):
        tb2_log_ctn.visible = True
        tb2_log_lv.controls.append(ft.Text(str(msg), color=ft.Colors.WHITE, size=12, font_family="monospace"))
        page.update()

    def mulai_trigger(e):
        if not tb2_cookie.value or not tb2_email.value:
            show_msg_dialog("❌ Cookie dan Email wajib diisi!"); return
        tb2_log_lv.controls.clear()
        log_tb2("⏳ Memulai proses trigger...")
        
        def worker():
            try:
                app = FBAccountsCenterTrigger(tb2_cookie.value, log_tb2)
                ok, status = app.run_trigger(tb2_email.value)
                
                if ok:
                    log_tb2("✅ Trigger berhasil dikirim!")
                    page.run_task(lambda: page.show_dialog(ft.SnackBar(ft.Text("✅ Trigger sukses! Cek email."))))
                else:
                    log_tb2(f"❌ Trigger gagal: {status}")
                    page.run_task(lambda: page.show_dialog(ft.SnackBar(ft.Text(f"❌ Gagal: {status}"))))
            except Exception as ex:
                log_tb2(f"❌ ERROR FATAL: {str(ex)}")
                page.run_task(lambda: page.show_dialog(ft.SnackBar(ft.Text(f"❌ Error: {ex}"))))
        threading.Thread(target=worker, daemon=True).start()

    tab2_content = ft.Column([
        ft.Text("Trigger Email Konfirmasi", weight=ft.FontWeight.BOLD),
        tb2_cookie, tb2_email,
        ft.Divider(),
        ft.Button(content=ft.Text("Mulai Trigger"), icon=ft.Icons.SEND, bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE, on_click=mulai_trigger),
        ft.Divider(),
        ft.Text("Log Proses:", weight=ft.FontWeight.BOLD),
        tb2_log_ctn
    ], scroll=ft.ScrollMode.AUTO)

    # ==========================================
    # TAB 3: SET DATA EMAIL
    # ==========================================
    tb3_uid = ft.TextField(label="UID")
    tb3_email = ft.TextField(label="Email")
    tb3_pin = ft.TextField(label="Kode Konfirmasi / PIN")

    def simpan_email_klik(e):
        if not tb3_uid.value or not tb3_email.value or not tb3_pin.value:
            show_msg_dialog("❌ Semua kolom wajib diisi!"); return
        simpan_data_email(tb3_uid.value, tb3_email.value, tb3_pin.value)
        show_msg_dialog("✅ Data email berhasil disimpan!")
        tb3_uid.value = tb3_email.value = tb3_pin.value = ""
        page.update()

    tab3_content = ft.Column([
        ft.Text("Masukkan Data Email & PIN", weight=ft.FontWeight.BOLD),
        tb3_uid, tb3_email, tb3_pin,
        ft.Button(content=ft.Text("Simpan ke Database"), on_click=simpan_email_klik, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
    ])

    # ==========================================
    # TAB 4: SET DOMAIN
    # ==========================================
    tb4_domain = ft.TextField(label="Domain (Cth: outlook.com)")
    list_domain_view = ft.ListView(expand=True, spacing=5)

    def refresh_domain():
        list_domain_view.controls.clear()
        for d in get_semua_domain(): list_domain_view.controls.append(ft.Text(f"🌐 {d}"))
        page.update()

    def tambah_domain_klik(e):
        if tb4_domain.value:
            tambah_domain(tb4_domain.value)
            tb4_domain.value = ""
            refresh_domain()

    refresh_domain()
    tab4_content = ft.Column([
        ft.Text("Tambah Domain Target", weight=ft.FontWeight.BOLD),
        ft.Row([tb4_domain, ft.Button(content=ft.Text("Tambah"), on_click=tambah_domain_klik)]),
        ft.Divider(),
        list_domain_view
    ])

    # ==========================================
    # TAB 5: DASHBOARD
    # ==========================================
    dashboard_list = ft.ListView(expand=True, spacing=10)
    tab5_content = ft.Column([ft.Text("Status Antrean", weight=ft.FontWeight.BOLD, size=18), dashboard_list])

    # ==========================================
    # SUSUNAN TAB
    # ==========================================
    tabs = ft.Tabs(
        selected_index=0,
        length=5,
        animation_duration=300,
        expand=1,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Auto Set"), ft.Tab(label="Trigger"),
                        ft.Tab(label="Set Email"), ft.Tab(label="Set Domain"),
                        ft.Tab(label="Dashboard")
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[tab1_content, tab2_content, tab3_content, tab4_content, tab5_content]
                )
            ]
        )
    )
    page.add(tabs)

    # ==========================================
    # LOGIKA DASHBOARD
    # ==========================================
    def tambah_ke_dashboard(tugas):
        uid = tugas['uid']
        waktu_str = datetime.fromtimestamp(tugas['waktu_mulai']).strftime('%H:%M:%S')
        teks_uid = ft.Text(uid, weight=ft.FontWeight.BOLD, size=16)
        teks_status = ft.Text(f"Status: {tugas['status']} (Mulai: {waktu_str})", color=ft.Colors.ORANGE)
        
        def hapus_item(e):
            if tugas in antrean_tugas: antrean_tugas.remove(tugas)
            kontainer_item.visible = False
            page.update()

        def stop_item(e):
            daftar_stop.add(uid)
            teks_status.value = "Status: Stopping..."
            page.update()

        kontainer_item = ft.Container(
            content=ft.Column([
                ft.Row([
                    teks_uid, 
                    ft.Button(content=ft.Text("Stop"), icon=ft.Icons.STOP, on_click=stop_item, bgcolor=ft.Colors.RED_400), 
                    ft.Button(content=ft.Text("Hapus"), icon=ft.Icons.DELETE, on_click=hapus_item)
                ]),
                teks_status
            ]),
            padding=10, border=ft.Border.all(1, ft.Colors.GREY), border_radius=8
        )
        dashboard_list.controls.append(kontainer_item)
        page.update()
        return teks_status, kontainer_item

    # ==========================================
    # LOGIKA EKSEKUSI TIAP AKUN (MULTI-THREAD)
    # ==========================================
    def jalankan_tugas(tugas, page_ref):
        uid, cookie = tugas['uid'], tugas['cookie']
        ui_status = tugas['_ui_status']
        
        # 1. Proses Timer
        while time.time() < tugas['waktu_mulai']:
            if uid in daftar_stop:
                tugas['status'] = 'Stopped'
                page_ref.run_task(_update_ui, ui_status, value="Status: Dihentikan User", color=ft.Colors.GREY)
                return
            
            selisih = int(tugas['waktu_mulai'] - time.time())
            page_ref.run_task(_update_ui, ui_status, value=f"Status: Waiting ({selisih} detik lagi)", color=ft.Colors.ORANGE)
            time.sleep(1)
        
        # 2. Mulai Eksekusi Program
        page_ref.run_task(_update_ui, ui_status, value="Status: Processing...", color=ft.Colors.BLUE)
        log_tb1(f"\n▶️ Memulai proses UID: {uid}")

        gagal_checkpoint = False
        for prog in tugas['program']:
            if uid in daftar_stop:
                page_ref.run_task(_update_ui, ui_status, value="Status: Dihentikan User", color=ft.Colors.GREY)
                log_tb1(f"⏹️ Proses UID {uid} dihentikan user.")
                return
            
            try:
                # Membuat fungsi log khusus untuk UID ini agar rapi di kotak hitam
                def make_logger(u):
                    return lambda m: log_tb1(f"[{u}] {m}")

                if prog == "A2F":
                    log_tb1(f"🔄 [{uid}] [A2F] Memproses...")
                    app = FBAccountsCenterA2F(cookie, make_logger(uid))
                    ok, status = app.run_a2f(tugas['password'])
                    if not ok and status == "checkpoint": gagal_checkpoint = True; break
                
                elif prog == "FOTO":
                    folder = tugas['folder_foto']
                    if not folder: continue
                    fotos = get_foto_di_folder(folder)
                    if not fotos: continue
                    nama_foto = random.choice(fotos)
                    path_foto = get_path_foto(folder, nama_foto)
                    
                    log_tb1(f"🖼️ [{uid}] [FOTO] Menggunakan: {nama_foto}")
                    app = FacebookProfileUploader(cookie, path_foto, make_logger(uid))
                    ok, status = app.run_upload()
                    if not ok and status == "checkpoint": gagal_checkpoint = True; break
                
                elif prog == "EMAIL":
                    log_tb1(f"🔄 [{uid}] [EMAIL] Memproses...")
                    data_email = ambil_dan_hapus_email(uid)
                    if not data_email:
                        log_tb1(f"❌ [{uid}] Data email kosong di DB!")
                        page_ref.run_task(_update_ui, ui_status, value="Status: Gagal (Email kosong)", color=ft.Colors.RED)
                        gagal_checkpoint = True; break
                    app = FBAccountsCenterEmail(cookie, make_logger(uid))
                    ok, status = app.run_ganti_email(data_email['email'], data_email['pin'])
                    if not ok and status == "checkpoint": gagal_checkpoint = True; break
                
                elif prog == "DELETE":
                    domain = tugas['domain']
                    if not domain: continue
                    log_tb1(f"🔄 [{uid}] [DELETE] Memproses...")
                    app = FBAccountsCenterDelete(cookie, make_logger(uid))
                    ok, status = app.run_delete(domain)
                    if not ok and status == "checkpoint": gagal_checkpoint = True; break

            except Exception as ex:
                log_tb1(f"❌ [{uid}] Error Fatal: {ex}")
                gagal_checkpoint = True
                break
            
            time.sleep(tugas['delay_prog'])

        # 3. Update Status Akhir
        if gagal_checkpoint:
            tugas['status'] = 'Gagal'
            page_ref.run_task(_update_ui, ui_status, value="Status: Gagal / Checkpoint", color=ft.Colors.RED)
            log_tb1(f"⛔ Proses UID {uid} dihentikan (Checkpoint).")
        elif uid not in daftar_stop:
            tugas['status'] = 'Sukses'
            page_ref.run_task(_update_ui, ui_status, value="Status: Sukses ✅", color=ft.Colors.GREEN)
            log_tb1(f"✅ Proses UID {uid} Selesai.")
        
        daftar_stop.discard(uid)

if __name__ == "__main__":
    ft.run(main)
