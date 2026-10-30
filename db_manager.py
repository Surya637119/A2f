import csv
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_A2F = os.path.join(APP_DIR, "database_a2f.csv")
DB_EMAIL = os.path.join(APP_DIR, "database_email.csv")
DB_DOMAIN = os.path.join(APP_DIR, "database_domain.csv")
FOTO_DIR = os.path.join(APP_DIR, "foto_upload")

# --- FUNGSI BANTU ---
def pastikan_file_ada(filepath, header):
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

# --- DATABASE A2F ---
def simpan_a2f(uid, email, kode_a2f):
    pastikan_file_ada(DB_A2F, ["UID", "Kosong", "Email", "Kode_A2F"])
    rows = []
    # Baca data lama
    if os.path.exists(DB_A2F):
        with open(DB_A2F, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
    # Cek apakah UID sudah ada, jika ada update
    found = False
    for i, row in enumerate(rows):
        if i > 0 and len(row) > 0 and row[0] == str(uid):
            rows[i] = [uid, "", email, kode_a2f]
            found = True
            break
            
    if not found:
        rows.append([uid, "", email, kode_a2f])
        
    # Tulis ulang
    with open(DB_A2F, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# --- DATABASE EMAIL ---
def simpan_data_email(uid, email, pin):
    pastikan_file_ada(DB_EMAIL, ["UID", "Email", "PIN"])
    rows = []
    if os.path.exists(DB_EMAIL):
        with open(DB_EMAIL, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            
    # Cek update
    found = False
    for i, row in enumerate(rows):
        if i > 0 and row[0] == str(uid):
            rows[i] = [uid, email, pin]
            found = True
            break
    if not found:
        rows.append([uid, email, pin])

    with open(DB_EMAIL, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)

def ambil_dan_hapus_email(uid):
    """Mengambil email & PIN, lalu langsung menghapusnya dari database"""
    if not os.path.exists(DB_EMAIL): return None
    rows = []
    data_ditemukan = None
    with open(DB_EMAIL, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
        
    new_rows = [rows[0]] # Simpan header
    for row in rows[1:]:
        if row[0] == str(uid):
            data_ditemukan = {"email": row[1], "pin": row[2]}
            # Tidak dimasukkan ke new_rows (berarti dihapus)
        else:
            new_rows.append(row)
            
    if data_ditemukan:
        with open(DB_EMAIL, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(new_rows)
            
    return data_ditemukan

# --- DATABASE DOMAIN ---
def tambah_domain(domain):
    pastikan_file_ada(DB_DOMAIN, ["Domain"])
    domains = get_semua_domain()
    if domain not in domains:
        with open(DB_DOMAIN, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([domain])

def get_semua_domain():
    if not os.path.exists(DB_DOMAIN): return []
    with open(DB_DOMAIN, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
        return [row[0] for row in rows[1:] if len(row) > 0]

# --- MANAJEMEN FOLDER FOTO ---
def get_semua_folder_foto():
    if not os.path.exists(FOTO_DIR):
        os.makedirs(FOTO_DIR, exist_ok=True)
    return [d for d in os.listdir(FOTO_DIR) if os.path.isdir(os.path.join(FOTO_DIR, d))]

def buat_folder_foto(nama_folder):
    path = os.path.join(FOTO_DIR, nama_folder)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        return True
    return False

def get_foto_di_folder(nama_folder):
    path = os.path.join(FOTO_DIR, nama_folder)
    if not os.path.exists(path): return []
    # Hanya ambil file gambar
    return [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
