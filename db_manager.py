import csv
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Mengambil path assets, jika kosong (None), fallback ke APP_DIR
ASSETS_DIR = os.getenv("FLET_ASSETS_DIR") or os.path.join(APP_DIR, "assets")

DB_A2F = os.path.join(APP_DIR, "database_a2f.csv")
DB_EMAIL = os.path.join(APP_DIR, "database_email.csv")
DB_DOMAIN = os.path.join(APP_DIR, "database_domain.csv")

def pastikan_file_ada(filepath, header):
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

def simpan_a2f(uid, password, email, kode_a2f):
    # Format: Kolom A (UID), Kolom B (Password), Kolom C (Email_Baru), Kolom D (Key_A2F)
    pastikan_file_ada(DB_A2F, ["UID", "Password", "Email_Baru", "Key_A2F"])
    rows = []
    if os.path.exists(DB_A2F):
        with open(DB_A2F, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            
    found = False
    for i, row in enumerate(rows):
        if i > 0 and len(row) > 0 and row[0] == str(uid):
            email_lama = row[2] if len(row) > 2 else ""
            email_final = email if email else email_lama
            rows[i] = [uid, password, email_final, kode_a2f]
            found = True
            break
            
    if not found: 
        rows.append([uid, password, email, kode_a2f])
        
    with open(DB_A2F, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)

def simpan_data_email(uid, email, pin):
    pastikan_file_ada(DB_EMAIL, ["UID", "Email", "PIN"])
    rows = []
    if os.path.exists(DB_EMAIL):
        with open(DB_EMAIL, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
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

def ambil_email(uid):
    if not os.path.exists(DB_EMAIL): return None
    with open(DB_EMAIL, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    for row in rows[1:]:
        if row[0] == str(uid): return {"email": row[1], "pin": row[2]}
    return None

def tambah_domain(domain):
    pastikan_file_ada(DB_DOMAIN, ["Domain"])
    if domain not in get_semua_domain():
        with open(DB_DOMAIN, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([domain])

def get_semua_domain():
    if not os.path.exists(DB_DOMAIN): return []
    with open(DB_DOMAIN, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
        return [row[0] for row in rows[1:] if len(row) > 0]

def get_semua_folder_foto():
     if not os.path.exists(ASSETS_DIR): return []
     return [d for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]

def get_foto_di_folder(nama_folder):
     path = os.path.join(ASSETS_DIR, nama_folder)
     if not os.path.exists(path): return []
     return [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

def get_path_foto(nama_folder, nama_file):
     return os.path.join(ASSETS_DIR, nama_folder, nama_file)

# Fungsi bantu untuk Share Database
def get_path_db_a2f():
    return DB_A2F
