import flet as ft
import os
import shutil
from db_manager import get_semua_folder_foto, buat_folder_foto, get_foto_di_folder, FOTO_DIR

def tampilkan_menu_upload(page: ft.Page, file_picker: ft.FilePicker):
    folder_target_upload = {"nama": None}
    input_folder_baru = ft.TextField(label="Nama Folder Baru (Cth: Laki Keren)", expand=True)
    list_folder_view = ft.ListView(expand=True, spacing=10)

    def refresh_daftar():
        list_folder_view.controls.clear()
        folders = get_semua_folder_foto()
        if not folders:
            list_folder_view.controls.append(ft.Text("Belum ada folder foto.", color=ft.Colors.GREY))
        
        for f in folders:
            jml_foto = len(get_foto_di_folder(f))
            
            def pilih_folder_upload(e, nama=f):
                folder_target_upload["nama"] = nama
                page.run_task(file_picker.pick_files, allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png"])

            def hapus_folder(e, nama=f):
                path = os.path.join(FOTO_DIR, nama)
                if os.path.exists(path):
                    shutil.rmtree(path)
                    refresh_daftar()
                    page.update()

            list_folder_view.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"📁 {f} ({jml_foto} foto)", weight=ft.FontWeight.BOLD, size=16),
                        ft.Row([
                            ft.Button(content=ft.Text("Upload Foto"), icon=ft.Icons.UPLOAD, on_click=pilih_folder_upload),
                            ft.Button(content=ft.Text("Hapus"), icon=ft.Icons.DELETE, bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE, on_click=hapus_folder)
                        ])
                    ]),
                    padding=10, 
                    border=ft.Border.all(1, ft.Colors.GREY_400), 
                    border_radius=10
                )
            )
        page.update()

    def on_pick_files_result(e: ft.FilePickerResultEvent):
        if e.files and folder_target_upload["nama"]:
            target_dir = os.path.join(FOTO_DIR, folder_target_upload["nama"])
            count = 0
            
            for f in e.files:
                try:
                    # FIX TOTAL: Gunakan fungsi baca Flet (bukan open() Python biasa)
                    # Ini dijamin tembus izin sandbox Android
                    file_bytes = f.read()
                    
                    if file_bytes:
                        dest_path = os.path.join(target_dir, f.name)
                        with open(dest_path, 'wb') as dst_file:
                            dst_file.write(file_bytes)
                        count += 1
                except Exception as ex:
                    print(f"Gagal copy {f.name}: {ex}")
                    
            folder_target_upload["nama"] = None
            refresh_daftar()
            page.show_dialog(ft.SnackBar(ft.Text(f"✅ {count} foto berhasil diupload!")))

    file_picker.on_result = on_pick_files_result

    def buat_folder_klik(e):
        nama = input_folder_baru.value.strip()
        if nama:
            if buat_folder_foto(nama):
                input_folder_baru.value = ""
                refresh_daftar()
            else:
                page.show_dialog(ft.SnackBar(ft.Text("❌ Folder sudah ada!")))

    tab_content = ft.Column([
        ft.Text("Manajemen Folder Foto", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([input_folder_baru, ft.Button(content=ft.Text("Buat Folder"), on_click=buat_folder_klik)]),
        ft.Divider(),
        list_folder_view
    ], expand=True)

    refresh_daftar()
    return tab_content
