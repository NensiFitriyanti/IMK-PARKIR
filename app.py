import streamlit as st
import pandas as pd
import uuid
import qrcode
from io import BytesIO
import os
from datetime import datetime, timedelta
import altair as alt
import numpy as np
import time
import bcrypt
import base64 # <-- Pastikan Base64 diimport di sini

# # --- KONFIGURASI APLIKASI ---
# DATA_FILE = 'parking_users.csv'
# LOG_FILE = 'parking_log.csv'

# # Memuat kredensial dari st.secrets.
# try:
#     ADMIN_USER = st.secrets.admin.username
#     ADMIN_PASS = st.secrets.secrets_pass.password
    
# except:
#     st.error("""
#         FATAL ERROR: Kredensial Admin tidak ditemukan.
#         Pastikan Anda memiliki file `.streamlit/secrets.toml` yang berisi:
#         [admin]
#         username = "..."
#         [secrets_pass]
#         password = "..." 
#     """)
#     st.stop()
    
# MONITOR_TIMEOUT_SECONDS = 5 # Durasi tampil pesan sukses di monitor (5 detik)

# REQUIRED_USER_COLUMNS = ['barcode_id', 'name', 'user_id', 'vehicle_type', 'license_plate', 'password', 'status', 'time_in', 'time_out', 'duration']
# REQUIRED_LOG_COLUMNS = ['event_id', 'barcode_id', 'name', 'timestamp', 'event_type']


# # -----------------------------------------------------------------------------
# # >>> FUNGSI UNTUK LATAR BELAKANG (BASE64 & BURAM) <<<
# # -----------------------------------------------------------------------------

# def get_base64_of_bin_file(bin_file):
#     """Membaca file dan mengkonversinya menjadi Base64 string."""
#     try:
#         with open(bin_file, 'rb') as f:
#             data = f.read()
#         return base64.b64encode(data).decode()
#     except FileNotFoundError: 
#         # Mengembalikan None jika file tidak ditemukan
#         print(f"Error: File gambar '{bin_file}' tidak ditemukan.")
#         return None

# def set_background(image_path):
#     """Menyuntikkan CSS untuk mengatur gambar latar belakang menggunakan Base64."""
    
#     base64_img = get_base64_of_bin_file(image_path)
    
#     # Perbaikan: Cek 'is not None' untuk menghindari NameError jika gagal membaca file
#     if base64_img is not None:
#         st.markdown(
#             f"""
#             <style>
#             .stApp {{
#                 /* Menggunakan data:image/jpeg;base64 untuk gambar yang tertanam */
#                 background-image: url("data:image/jpeg;base64,{base64_img}");
#                 background-size: cover; 
#                 background-attachment: fixed; 
#                 background-position: center;
#             }}
#             /* 1. Sidebar Transparan (Opacity 80%) */
#             [data-testid="stSidebar"] {{
#                 background-color: rgba(255, 255, 255, 0.8); 
#                 border-right: 1px solid #ccc;
#             }}

#             /* 2. AREA KONTEN UTAMA DIBUAT BURAM (Opacity 90%) */
#             /* stVerticalBlock adalah container utama untuk konten dashboard */
#             [data-testid="stVerticalBlock"] {{
#                 background-color: rgba(255, 255, 255, 0.9);
#                 padding: 10px 20px 20px 20px; 
#                 border-radius: 10px; 
#             }}
            
#             /* 3. Teks Berbayangan agar tetap terbaca di atas gambar/kontainer buram */
#             h1, h2, h3, p, .stMarkdown, .css-1d3f9b, .css-1dp5vir {{
#                 color: #333333; 
#                 text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.7); 
#             }}
#             </style>
#             """,
#             unsafe_allow_html=True
#         )
#     else:
#         st.warning(f"File '{image_path}' tidak ditemukan. Latar belakang default (putih) digunakan.")
        
# # -----------------------------------------------------------------------------
# # >>> FUNGSI UNTUK LATAR BELAKANG SELESAI DI SINI <<<
# # -----------------------------------------------------------------------------


# # --- FUNGSI UTAMA (DEFAULT MONITOR MESSAGE) ---

# def get_default_monitor_message():
#     """Mengembalikan HTML untuk pesan monitor default (Scan Here)."""
#     return (
#         f"<div style='background-color: #f1f3f5; color: #495057; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"
#         f"<h1 style='margin: 0; font-size: 80px;'>SCAN BARCODE ANDA</h1>"
#         f"<p style='font-size: 30px;'>Arahkan Barcode ke Kamera/Scanner</p>"
#         f"<div style='width: 250px; height: 150px; border: 10px solid #495057; margin: 20px auto; border-radius: 10px;'></div>" 
#         f"</div>"
#     )

# # --- FUNGSI PEMBANTU (UTILITIES) ---

# def hash_password(password):
#     """Menghasilkan hash dari password menggunakan bcrypt."""
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# def check_password(plain_password, hashed_password):
#     """Memverifikasi password yang dimasukkan dengan hash yang tersimpan."""
#     try:
#         return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
#     except (ValueError, TypeError):
#         return False
        
# def load_data(file_name, required_cols):
#     """Memuat data dari CSV atau membuat DataFrame baru, dan memastikan semua kolom penting ada."""
    
#     if os.path.exists(file_name):
#         df = pd.read_csv(file_name)
        
#         for col in required_cols:
#             if col not in df.columns:
#                 df[col] = '' 
        
#         for col in ['user_id', 'name', 'password']:
#             if col in df.columns:
#                 df[col] = df[col].astype(str).fillna('')
            
#         for col in ['timestamp', 'time_in', 'time_out']:
#             if col in df.columns:
#                 df[col] = pd.to_datetime(df[col], errors='coerce')
            
#         if 'barcode_id' in df.columns:
#             df = df.set_index('barcode_id', drop=False)
            
#     else:
#         df = pd.DataFrame(columns=required_cols)
#         if 'barcode_id' in required_cols:
#             df.set_index('barcode_id', drop=False, inplace=True)
    
#     return df

# def save_data(df, file_name):
#     """Menyimpan DataFrame ke CSV."""
#     df.to_csv(file_name, index=False)

# def generate_qr_code(data):
#     """Menghasilkan gambar QR code (Barcode) di memori."""
#     qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,)
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color="black", back_color="white")
#     buffer = BytesIO()
#     img.save(buffer, format="PNG")
#     buffer.seek(0)
#     return buffer

# def add_to_log(barcode_id, name, event_type, timestamp):
#     """Menambahkan entri baru ke tabel log."""
#     new_log = {
#         'event_id': str(uuid.uuid4()),
#         'barcode_id': barcode_id,
#         'name': name,
#         'timestamp': timestamp,
#         'event_type': event_type
#     }
#     # Menggunakan pd.concat untuk menambah baris
#     new_log_df = pd.DataFrame([new_log], columns=st.session_state.log.columns)
#     st.session_state.log = pd.concat([st.session_state.log, new_log_df], ignore_index=True)
#     save_data(st.session_state.log, LOG_FILE)

# def set_monitor_message(html_content, type='default'):
#     """Menyimpan pesan HTML untuk ditampilkan di Gate Monitor dan mereset timer."""
#     st.session_state.monitor_html = html_content
#     st.session_state.monitor_type = type
#     st.session_state.monitor_display_time = datetime.now() 

# def process_scan(scan_id, feedback_placeholder):
#     """
#     Logika utama untuk memproses ID Barcode yang diterima.
#     Fungsi ini akan mengatur pesan monitor.
#     """
    
#     # Check 1: ID Barcode kosong atau simulasi
#     if not scan_id or scan_id in ["simulasi1234", "simulasi_camera_id_12345"]: 
#         feedback_placeholder.error("ID Barcode kosong atau tidak valid.")
#         set_monitor_message(
#             f"<div style='background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
#             f"<h1 style='margin: 0; font-size: 80px;'>❌ ERROR!</h1>"\
#             f"<p style='font-size: 40px; font-weight: bold;'>BARCODE TIDAK VALID / KOSONG</p>"\
#             f"</div>", 'ERROR'
#         )
#         # PENTING: Paksakan transisi ke Monitor
#         st.session_state.app_mode = 'gate_monitor'
#         return 

        
#     # Check 2: ID Barcode terdaftar
#     if scan_id in st.session_state.data.index:
#         user_row = st.session_state.data.loc[scan_id]
#         current_status = user_row['status']
#         current_time = datetime.now()
#         name = user_row['name']
#         license_plate = user_row['license_plate']
        
#         # Logika Pintu Masuk/Keluar
#         if current_status == 'OUT':
#             # Aksi MASUK
#             st.session_state.data.loc[scan_id, 'status'] = 'IN'
#             st.session_state.data.loc[scan_id, 'time_in'] = current_time 
#             st.session_state.data.loc[scan_id, 'time_out'] = pd.NaT      
#             st.session_state.data.loc[scan_id, 'duration'] = ''          
#             save_data(st.session_state.data, DATA_FILE)
#             add_to_log(scan_id, name, 'IN', current_time)

#             # Update Monitor (Pesan Selamat Datang)
#             set_monitor_message(
#                 f"<div style='background-color: #d4edda; color: #155724; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
#                 f"<h1 style='margin: 0; font-size: 80px;'>✅ SELAMAT DATANG!</h1>"\
#                 f"<p style='margin-top: 20px; font-size: 50px; font-weight: bold;'>{name}</p>"\
#                 f"<p style='font-size: 40px;'>({license_plate})</p>"\
#                 f"</div>", 'IN'
#             )
#             feedback_placeholder.success(f"GERBANG TERBUKA! {name} masuk.")
            
#         else: # Status is 'IN'
#             # Aksi KELUAR
#             time_in = st.session_state.data.loc[scan_id, 'time_in']
            
#             if pd.notna(time_in) and isinstance(time_in, datetime):
#                 duration = current_time - time_in
#                 duration_str = str(duration).split('.')[0] 
#             else:
#                 duration_str = "0:00:00 (Error Waktu Masuk)"
            
#             st.session_state.data.loc[scan_id, 'status'] = 'OUT'
#             st.session_state.data.loc[scan_id, 'time_out'] = current_time 
#             st.session_state.data.loc[scan_id, 'duration'] = duration_str 
#             save_data(st.session_state.data, DATA_FILE)
#             add_to_log(scan_id, name, 'OUT', current_time)

#             # Update Monitor (Pesan Sampai Jumpa)
#             set_monitor_message(
#                 f"<div style='background-color: #fff3cd; color: #856404; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
#                 f"<h1 style='margin: 0; font-size: 80px;'>🚪 SAMPAI JUMPA LAGI</h1>"\
#                 f"<p style='margin-top: 20px; font-size: 50px; font-weight: bold;'>{name}</p>"\
#                 f"<p style='font-size: 40px;'>({license_plate})</p>"\
#                 f"<p style='font-size: 25px;'>Durasi Parkir: {duration_str}</p>"\
#                 f"</div>", 'OUT'
#             )
#             feedback_placeholder.info(f"GERBANG TERBUKA! {name} keluar. Durasi: {duration_str}")
        
#         # PENTING: Paksakan transisi ke Monitor setelah status berhasil diubah
#         st.session_state.app_mode = 'gate_monitor'
#         return 

#     else:
#         # Pesan Barcode Tidak Terdaftar
#         set_monitor_message(
#             f"<div style='background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
#             f"<h1 style='margin: 0; font-size: 80px;'>❌ ERROR!</h1>"\
#             f"<p style='font-size: 40px; font-weight: bold;'>BARCODE TIDAK TERDAFTAR</p>"\
#             f"</div>", 'ERROR'
#         )
#         feedback_placeholder.error("❌ Barcode ID tidak terdaftar!")
#         # PENTING: Paksakan transisi ke Monitor
#         st.session_state.app_mode = 'gate_monitor'
#         return


# # --- INISIALISASI APLIKASI DAN SESSION STATE ---
# st.set_page_config(layout="wide", page_title="Dashboard Parkir Barcode")

# # -----------------------------------------------------------------------------
# # >>> PEMANGGILAN FUNGSI LATAR BELAKANG DITAMBAHKAN DI SINI <<<
# set_background('BG-FASILKOM.jpeg') 
# # -----------------------------------------------------------------------------

# if 'data' not in st.session_state:
#     st.session_state.data = load_data(DATA_FILE, REQUIRED_USER_COLUMNS)
# if 'log' not in st.session_state:
#     st.session_state.log = load_data(LOG_FILE, REQUIRED_LOG_COLUMNS)

# if 'app_mode' not in st.session_state:
#     st.session_state.app_mode = 'login'
# if 'logged_in_user_id' not in st.session_state:
#     st.session_state.logged_in_user_id = None
# if 'user_role' not in st.session_state:
#     st.session_state.user_role = None  
    
# # --- INISIALISASI MONITOR STATE ---
# if 'monitor_html' not in st.session_state:
#     st.session_state.monitor_html = get_default_monitor_message()  
    
# if 'monitor_type' not in st.session_state:    
#     st.session_state.monitor_type = 'default'    

# if 'monitor_display_time' not in st.session_state:
#     st.session_state.monitor_display_time = datetime.now() - timedelta(seconds=MONITOR_TIMEOUT_SECONDS + 1)
    
# if 'admin_table_filter' not in st.session_state:
#     st.session_state.admin_table_filter = 'ALL' 
    
# # Tombol Logout dan Menu Admin/Monitor
# st.sidebar.title("Menu Aplikasi")

# if st.session_state.app_mode == 'gate_monitor':
#     st.sidebar.markdown("**Monitor Sedang Aktif**")
#     if st.sidebar.button("Kembali ke Dashboard Admin"):
#         st.session_state.app_mode = 'admin_dashboard'
#         st.rerun()
# elif st.session_state.app_mode not in ['login', 'register']:
#     if st.session_state.user_role == 'admin':
#         if st.sidebar.button("Dashboard Petugas"):
#             st.session_state.app_mode = 'admin_dashboard'
#             st.rerun()
#         if st.sidebar.button("Analitik & Grafik"):
#             st.session_state.app_mode = 'admin_analytics'
#             st.rerun()
#         if st.sidebar.button("Reset Password Pengguna"):
#             st.session_state.app_mode = 'admin_reset_password'
#             st.rerun()
#         st.sidebar.markdown("---")
#         if st.sidebar.button("Buka Monitor Gerbang"):
#              st.session_state.app_mode = 'gate_monitor'
#              st.rerun()
#         st.sidebar.markdown("---")

#     if st.sidebar.button("Logout"):
#         st.session_state.app_mode = 'login'
#         st.session_state.logged_in_user_id = None
#         st.session_state.user_role = None
#         st.rerun()    

# if st.session_state.app_mode != 'gate_monitor':
#     st.title("🅿️ Aplikasi Parkir Barcode")
#     st.markdown("---")

# # =================================================================
# # FUNGSI APLIKASI BERDASARKAN MODE
# # =================================================================

# # ----------------- MODE MONITOR GERBANG (Logika Timer Stabil) -----------------
# if st.session_state.app_mode == 'gate_monitor':
    
#     # Hitung waktu yang berlalu sejak pesan terakhir ditampilkan
#     time_elapsed = datetime.now() - st.session_state.monitor_display_time
    
#     # Cek apakah waktu sudah melewati batas timeout (5 detik)
#     if st.session_state.monitor_type != 'default' and time_elapsed.total_seconds() >= MONITOR_TIMEOUT_SECONDS:
        
#         # 1. Reset pesan ke default
#         st.session_state.monitor_html = get_default_monitor_message()
#         st.session_state.monitor_type = 'default'
        
#         # 2. Reset display time ke waktu lampau agar tidak terjadi loop reset
#         st.session_state.monitor_display_time = datetime.now() - timedelta(seconds=MONITOR_TIMEOUT_SECONDS + 1)
        
#         # 3. PENTING: Paksa RERUN untuk menampilkan pesan default
#         st.rerun() 
        
#     # Tampilkan pesan monitor
#     st.markdown(
#         st.session_state.monitor_html, 
#         unsafe_allow_html=True
#     )
    
#     # Logika RERUN Otomatis untuk menghitung mundur
#     if st.session_state.monitor_type != 'default' and time_elapsed.total_seconds() < MONITOR_TIMEOUT_SECONDS:
        
#         # Tampilkan hitungan mundur 
#         time_left = MONITOR_TIMEOUT_SECONDS - int(time_elapsed.total_seconds())
#         st.empty().markdown(
#             f"<div style='text-align: right; color: gray;'>⏳ Kembali dalam {time_left} detik...</div>", 
#             unsafe_allow_html=True
#         )
        
#         # Tunggu 1 detik
#         time.sleep(1) 
        
#         # PENTING: Paksa Streamlit untuk menjalankan ulang skrip agar cek waktu berikutnya
#         st.rerun() 
    
#     st.stop() 

# # ----------------- MODE LOGIN / REGISTER / USER DASHBOARD -----------------
# elif st.session_state.app_mode == 'login':
#     st.subheader("Selamat Datang! Silakan Login atau Daftar")
#     col_l, col_r = st.columns(2)

#     with col_l:
#         with st.form("login_form"):
#             st.write("### Login Pengguna/Petugas")
            
#             login_name_or_admin = st.text_input("Nama Lengkap Anda (atau 'petugas')", key="login_id").strip()
#             login_pass = st.text_input("Password", type="password", key="login_pass")
#             login_button = st.form_submit_button("Login")
            
#             if login_button:
                
#                 # 1. Cek login Admin
#                 if login_name_or_admin == ADMIN_USER and login_pass == ADMIN_PASS:
#                     st.session_state.app_mode = 'admin_dashboard'
#                     st.session_state.user_role = 'admin'
#                     st.success("Login sebagai Petugas/Admin berhasil!")
#                     st.rerun()
#                   # 2. Cek login Pengguna Biasa
#                 else:
#                     found_user = st.session_state.data[
#                         st.session_state.data['name'].str.lower() == login_name_or_admin.lower()
#                     ]
                
#                     if not found_user.empty:
#                         first_match = found_user.iloc[0]
#                         stored_password_clean = str(first_match['password']).strip()
                        
#                         if stored_password_clean and check_password(login_pass, stored_password_clean):
#                             st.session_state.app_mode = 'user_dashboard'
#                             st.session_state.user_role = 'user'
#                             st.session_state.logged_in_user_id = first_match['barcode_id'] 
#                             st.success(f"Login pengguna {first_match['name']} berhasil!")
#                             st.rerun()
#                         else:
#                             st.error("Password salah!") 
#                     else:
#                         st.error("Nama Lengkap tidak terdaftar!")
                
#                 # ==========================
#                 # Tombol Daftar Akun Baru di bawah dan tengah
#                 # ==========================
                
#                 st.markdown("<br>", unsafe_allow_html=True)  # beri sedikit jarak dari form login
                
#                 # Buat 3 kolom agar tombol di tengah
#                 col1, col2, col3 = st.columns([1, 2, 1])
#                 with col2:
#                     daftar_clicked = st.button("Daftar Akun Baru (Register)", use_container_width=True)
#                     if daftar_clicked:
#                         st.session_state.app_mode = 'register'
#                         st.rerun()
  

#     #             # 2. Cek login Pengguna Biasa
#     #             else:
#     #                 found_user = st.session_state.data[
#     #                     st.session_state.data['name'].str.lower() == login_name_or_admin.lower()
#     #                 ]

#     #                 if not found_user.empty:
#     #                     first_match = found_user.iloc[0]

#     #                     stored_password_clean = str(first_match['password']).strip()
                        
#     #                     if stored_password_clean and check_password(login_pass, stored_password_clean):
#     #                         st.session_state.app_mode = 'user_dashboard'
#     #                         st.session_state.user_role = 'user'
#     #                         st.session_state.logged_in_user_id = first_match['barcode_id'] 
#     #                         st.success(f"Login pengguna {first_match['name']} berhasil!")
#     #                         st.rerun()
#     #                     else:
#     #                         st.error("Password salah!") 
#     #                 else:
#     #                     st.error("Nama Lengkap tidak terdaftar!")


#     # with col_r:
#     #     if st.button("Daftar Akun Baru (Register)"):
#     #         st.session_state.app_mode = 'register'
#     #         st.rerun()




# elif st.session_state.app_mode == 'user_dashboard' and st.session_state.user_role == 'user':
#     user_id = st.session_state.logged_in_user_id
#     if user_id not in st.session_state.data.index:
#         st.error("Data pengguna tidak ditemukan. Silakan login ulang.")
#         st.session_state.app_mode = 'login'
#         st.rerun()
    
#     user_data = st.session_state.data.loc[user_id]
    
#     st.header(f"Selamat Datang di Dashboard Anda, {user_data['name']}!")
    
#     col_info, col_qr = st.columns([1, 1])
    
#     with col_info:
#         st.subheader("Identitas dan Data Kendaraan")
#         st.markdown(f"**Nama Lengkap:** {user_data['name']}")
#         st.markdown(f"**NIM/NIP:** {user_data['user_id']}")
#         st.markdown(f"**Jenis Kendaraan:** {user_data['vehicle_type']}")
#         st.markdown(f"**Nomor Polisi:** {user_data['license_plate']}")
#         st.markdown(f"**Status Parkir Saat Ini:** **{user_data['status']}**")
        
#         st.markdown("---")
#         st.subheader("Informasi Waktu")
        
#         if pd.notna(user_data['time_in']):
#             st.markdown(f"**Waktu Masuk:** {user_data['time_in'].strftime('%d %b %Y, %H:%M:%S')}")
#         else:
#             st.markdown(f"**Waktu Masuk:** Belum ada data masuk.")
            
#         if user_data['status'] == 'OUT' and pd.notna(user_data['time_out']):
#             st.markdown(f"**Waktu Keluar:** {user_data['time_out'].strftime('%d %b %Y, %H:%M:%S')}")
#             st.success(f"**Durasi Parkir:** {user_data['duration']}")

#     with col_qr:
#         st.subheader("Barcode Akses Parkir (Kunci Gerbang)")
#         st.info("Tunjukkan Barcode ini ke scanner di gerbang untuk masuk/keluar.")
        
#         qr_buffer = generate_qr_code(user_id)
#         st.image(qr_buffer, caption=f"ID: {user_id[:8]}...", width=250)
        
#         st.download_button(
#             label="Download Barcode (PNG)",
#             data=qr_buffer,
#             file_name=f"{user_data['name']}_parkir.png",
#             mime="image/png"
#         )
# ==============================================================
# 🅿️ APLIKASI PARKIR BARCODE (Versi Stabil dan Rapi)
# ==============================================================
import streamlit as st
import pandas as pd
import bcrypt, qrcode, base64, os, time, uuid
from io import BytesIO
from datetime import datetime, timedelta

# --------------------------------------------------------------
# KONFIGURASI DASAR
# --------------------------------------------------------------
DATA_FILE = 'parking_users.csv'
LOG_FILE = 'parking_log.csv'

try:
    ADMIN_USER = st.secrets.admin.username
    ADMIN_PASS = st.secrets.secrets_pass.password
except Exception:
    st.error("""
        ❌ **FATAL ERROR**: File `.streamlit/secrets.toml` tidak ditemukan atau format salah.
        Pastikan isi file:
        ```
        [admin]
        username = "admin"
        [secrets_pass]
        password = "12345"
        ```
    """)
    st.stop()

MONITOR_TIMEOUT_SECONDS = 5

REQUIRED_USER_COLUMNS = [
    'barcode_id', 'name', 'user_id', 'vehicle_type',
    'license_plate', 'password', 'status', 'time_in', 'time_out', 'duration'
]
REQUIRED_LOG_COLUMNS = ['event_id', 'barcode_id', 'name', 'timestamp', 'event_type']

# --------------------------------------------------------------
# FUNGSI LATAR BELAKANG
# --------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def set_background(image_path):
    base64_img = get_base64_of_bin_file(image_path)
    if base64_img:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{base64_img}");
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }}
            [data-testid="stSidebar"] {{
                background-color: rgba(255, 255, 255, 0.8);
            }}
            [data-testid="stVerticalBlock"] {{
                background-color: rgba(255,255,255,0.9);
                border-radius: 12px;
                padding: 20px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ Gambar latar tidak ditemukan. Menggunakan warna putih.")

# --------------------------------------------------------------
# FUNGSI UTILITAS
# --------------------------------------------------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def load_data(file_name, required_cols):
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
    else:
        df = pd.DataFrame(columns=required_cols)
    if 'barcode_id' in df.columns:
        df.set_index('barcode_id', drop=False, inplace=True)
    return df

def save_data(df, file_name):
    df.to_csv(file_name, index=False)

def generate_qr_code(data):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# --------------------------------------------------------------
# INISIALISASI STATE
# --------------------------------------------------------------
st.set_page_config(page_title="Aplikasi Parkir Barcode", layout="wide")
set_background("BG-FASILKOM.jpeg")

if 'data' not in st.session_state:
    st.session_state.data = load_data(DATA_FILE, REQUIRED_USER_COLUMNS)
if 'log' not in st.session_state:
    st.session_state.log = load_data(LOG_FILE, REQUIRED_LOG_COLUMNS)
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'login'
if 'logged_in_user_id' not in st.session_state:
    st.session_state.logged_in_user_id = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --------------------------------------------------------------
# SIDEBAR MENU
# --------------------------------------------------------------
st.sidebar.title("Menu Aplikasi")

if st.session_state.app_mode not in ['login', 'register']:
    if st.sidebar.button("🏠 Dashboard Utama"):
        st.session_state.app_mode = 'admin_dashboard' if st.session_state.user_role == 'admin' else 'user_dashboard'
        st.rerun()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.app_mode = 'login'
        st.session_state.user_role = None
        st.session_state.logged_in_user_id = None
        st.rerun()

# --------------------------------------------------------------
# HALAMAN LOGIN
# --------------------------------------------------------------
if st.session_state.app_mode == 'login':
    st.title("🅿️ Aplikasi Parkir Barcode")
    st.subheader("Selamat Datang! Silakan Login")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("login_form"):
            username = st.text_input("Nama Lengkap (atau 'petugas')").strip()
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                # Admin
                if username == ADMIN_USER and password == ADMIN_PASS:
                    st.session_state.app_mode = 'admin_dashboard'
                    st.session_state.user_role = 'admin'
                    st.success("Login sebagai Admin berhasil!")
                    st.rerun()
                # Pengguna biasa
                else:
                    df = st.session_state.data
                    match = df[df['name'].str.lower() == username.lower()]
                    if not match.empty:
                        user = match.iloc[0]
                        if check_password(password, str(user['password'])):
                            st.session_state.app_mode = 'user_dashboard'
                            st.session_state.user_role = 'user'
                            st.session_state.logged_in_user_id = user['barcode_id']
                            st.success("Login pengguna berhasil!")
                            st.rerun()
                        else:
                            st.error("Password salah!")
                    else:
                        st.error("Nama tidak ditemukan.")

    st.markdown("---")
    st.markdown("<div style='text-align:center;'>Belum punya akun?</div>", unsafe_allow_html=True)
    if st.button("🆕 Daftar Akun Baru"):
        st.session_state.app_mode = 'register'
        st.rerun()

# --------------------------------------------------------------
# HALAMAN REGISTER
# --------------------------------------------------------------
elif st.session_state.app_mode == 'register':
    st.title("🆕 Pendaftaran Akun Pengguna Baru")

    with st.form("register_form"):
        name = st.text_input("Nama Lengkap")
        user_id = st.text_input("NIM/NIP")
        vehicle = st.selectbox("Jenis Kendaraan", ["Motor", "Mobil"])
        plate = st.text_input("Nomor Polisi")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Konfirmasi Password", type="password")

        submit = st.form_submit_button("Daftar")

        if submit:
            if not all([name, user_id, vehicle, plate, password]):
                st.warning("Harap isi semua kolom.")
            elif password != confirm:
                st.error("Password tidak sama.")
            else:
                df = st.session_state.data
                new_id = str(uuid.uuid4())
                df.loc[new_id] = [
                    new_id, name, user_id, vehicle, plate,
                    hash_password(password), 'OUT', '', '', ''
                ]
                save_data(df, DATA_FILE)
                st.success("Pendaftaran berhasil! Silakan login.")
                st.session_state.app_mode = 'login'
                st.rerun()

    if st.button("⬅️ Kembali ke Login"):
        st.session_state.app_mode = 'login'
        st.rerun()

# --------------------------------------------------------------
# HALAMAN USER DASHBOARD
# --------------------------------------------------------------
elif st.session_state.app_mode == 'user_dashboard' and st.session_state.user_role == 'user':
    df = st.session_state.data
    user = df.loc[st.session_state.logged_in_user_id]

    st.header(f"Selamat Datang, {user['name']}!")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nomor Polisi:** {user['license_plate']}")
        st.markdown(f"**Jenis Kendaraan:** {user['vehicle_type']}")
        st.markdown(f"**Status Parkir:** {user['status']}")
    with col2:
        qr = generate_qr_code(user['barcode_id'])
        st.image(qr, caption="Barcode Akses Parkir", width=200)
        st.download_button("Download Barcode", data=qr, file_name=f"{user['name']}.png", mime="image/png")

# --------------------------------------------------------------
# HALAMAN ADMIN DASHBOARD (SEMENTARA)
# --------------------------------------------------------------
elif st.session_state.app_mode == 'admin_dashboard':
    st.title("📊 Dashboard Admin")
    st.write("Daftar Pengguna Terdaftar:")
    st.dataframe(st.session_state.data)


# ----------------- DASHBOARD ADMIN/PETUGAS -----------------
elif st.session_state.app_mode == 'admin_dashboard' and st.session_state.user_role == 'admin':
    st.header("Dashboard Petugas Parkir (Akses Admin)")
    
    col_input, col_stats = st.columns([6, 2])

    with col_input:
        st.subheader("Kontrol Scanner Gerbang")
        
        feedback_placeholder = st.empty()
        
        tab_text, tab_file, tab_camera = st.tabs(["Input Teks ID", "Unggah Barcode Gambar", "Ambil Foto Barcode (Kamera)"])

        with tab_text:
            scan_id_text = st.text_input("Masukkan Barcode ID Manual:", key="admin_scan_id_text").strip()
            if st.button("PROSES DENGAN TEKS"):
                # Panggil process_scan, lalu paksa transisi mode dan rerun
                process_scan(scan_id_text, feedback_placeholder)
                st.session_state.app_mode = 'gate_monitor' 
                st.rerun() 
                

        with tab_file:
            uploaded_file = st.file_uploader("Unggah Gambar Barcode/QR Code (.png, .jpg)", type=['png', 'jpg', 'jpeg'])
            if uploaded_file is not None:
                simulated_id = uploaded_file.name.split('.')[0] 
                st.info(f"Simulasi: ID Barcode yang terdeteksi adalah **{simulated_id}** (berdasarkan nama file).")
                if st.button("PROSES DENGAN GAMBAR"):
                    # Panggil process_scan, lalu paksa transisi mode dan rerun
                    process_scan(simulated_id, feedback_placeholder)
                    st.session_state.app_mode = 'gate_monitor' 
                    st.rerun()
                    

        with tab_camera:
            camera_image = st.camera_input("Arahkan Kamera ke Barcode", help="Fitur ini menggunakan kamera perangkat Anda. Pastikan Barcode terlihat jelas.")
            if camera_image is not None:
                # Menggunakan ID simulasi. Pastikan ini ID yang valid jika Anda mengujinya.
                simulated_id_cam = "simulasi1234" 
                st.image(camera_image, caption="Foto Barcode yang diambil", use_column_width=True)
                st.warning(f"Simulasi: ID Barcode yang terdeteksi adalah **{simulated_id_cam}**.")
                if st.button("PROSES DENGAN FOTO"):
                    # Panggil process_scan, lalu paksa transisi mode dan rerun
                    process_scan(simulated_id_cam, feedback_placeholder)
                    st.session_state.app_mode = 'gate_monitor' 
                    st.rerun()


    # Statistik Dashboard
    with col_stats:
        st.subheader("Ringkasan Status")
        total_users = len(st.session_state.data)
        parked_count = len(st.session_state.data[st.session_state.data['status'] == 'IN'])
        out_count = total_users - parked_count

        st.metric(label="Total Pengguna Terdaftar", value=total_users)
        st.metric(label="Sedang Parkir (IN)", value=parked_count)
        st.metric(label="Sudah Keluar (OUT)", value=out_count)

    if feedback_placeholder.empty:
        feedback_placeholder.markdown("Siap untuk *scan* berikutnya...", unsafe_allow_html=True)
            
    st.markdown("---") 
    
    # Tabel Status Parkir & Hapus Akun
    st.subheader("Tabel Status Parkir Saat Ini")
    
    def set_filter(status):
        st.session_state.admin_table_filter = status
    
    col_filter_all, col_filter_in, col_filter_out, col_spacer = st.columns([2, 2, 2, 5])
    with col_filter_all:
        if st.button("🌎 Semua", key="filter_all"):
            set_filter('ALL')
    with col_filter_in:
        if st.button("🚗 Masuk", key="filter_in"):
            set_filter('IN')
    with col_filter_out:
        if st.button("🚪 Keluar", key="filter_out"):
            set_filter('OUT')

    df_filtered_table = st.session_state.data.copy()
    if st.session_state.admin_table_filter == 'IN':
        df_filtered_table = df_filtered_table[df_filtered_table['status'] == 'IN']
        st.info("Filter Aktif: Hanya menampilkan yang sedang **Masuk (IN)**.")
    elif st.session_state.admin_table_filter == 'OUT':
        df_filtered_table = df_filtered_table[df_filtered_table['status'] == 'OUT']
        st.info("Filter Aktif: Hanya menampilkan yang sudah **Keluar (OUT)**.")
    else:
        st.info("Filter Aktif: Menampilkan **Semua** data pengguna.")
        
    display_data = df_filtered_table[['name', 'user_id', 'license_plate', 'status', 'time_in', 'time_out', 'duration']].copy()
    
    display_data['time_in'] = pd.to_datetime(display_data['time_in'], errors='coerce').dt.strftime('%H:%M:%S, %d/%m').fillna('-')
    display_data['time_out'] = pd.to_datetime(display_data['time_out'], errors='coerce').dt.strftime('%H:%M:%S, %d/%m').fillna('-')

    def color_status(val):
        color = 'lightgreen' if val == 'IN' else 'salmon'
        return f'background-color: {color}'

    st.dataframe(
        display_data.style.applymap(color_status, subset=['status']),
        use_container_width=True
    )
    
    
    st.markdown("---")
    
    
    # LOGIKA PENGHAPUSAN AKUN OLEH ADMIN
    st.subheader("Opsi Admin: Hapus Akun Pengguna")
    
    user_list = [name for name in st.session_state.data['name'].tolist() if name.lower() != ADMIN_USER.lower()]
    user_to_delete_name = st.selectbox("Pilih Pengguna yang akan dihapus:", [''] + user_list, key="delete_user_select")
    
    delete_button = st.button("Hapus Akun Pengguna Terpilih", disabled=(user_to_delete_name == ''))
    
    if delete_button and user_to_delete_name:
                try:
                    user_rows = st.session_state.data[
                        st.session_state.data['name'].str.lower() == user_to_delete_name.lower()
                    ]
        
                    if not user_rows.empty:
                        barcode_to_delete = user_rows.iloc[0]['barcode_id']
        
                        # Hapus dari data utama
                        st.session_state.data = st.session_state.data.drop(barcode_to_delete, errors='ignore')
                        save_data(st.session_state.data, DATA_FILE)
        
                        # Hapus juga semua log terkait pengguna itu
                        st.session_state.log = st.session_state.log[
                            st.session_state.log['barcode_id'] != barcode_to_delete
                        ]
                        save_data(st.session_state.log, LOG_FILE)
        
                        st.success(f"Akun '{user_to_delete_name}' dan seluruh log-nya telah dihapus.")
                        st.rerun()
                    else:
                        st.warning("Pengguna tidak ditemukan dalam database.")
                except Exception as e:
                    st.error(f"Gagal menghapus pengguna: {e}")
        
                # try:
        #     user_rows = st.session_state.data[st.session_state.data['name'] == user_to_delete_name]
        #     barcode_id_to_delete = user_rows.index.tolist()
            
        #     st.session_state.data.drop(index=barcode_id_to_delete, inplace=True)
        #     save_data(st.session_state.data, DATA_FILE)

        #     st.session_state.log = st.session_state.log[~st.session_state.log['barcode_id'].isin(barcode_id_to_delete)]
        #     save_data(st.session_state.log, LOG_FILE)
            
        #     st.success(f"Akun pengguna {user_to_delete_name} (dan {len(barcode_id_to_delete)} data terkait) berhasil dihapus.")
        #     st.rerun()
            
        # except Exception as e:
        #     st.error(f"Terjadi masalah saat penghapusan: {e}")


# ----------------- ADMIN RESET PASSWORD -----------------
elif st.session_state.app_mode == 'admin_reset_password' and st.session_state.user_role == 'admin':
    
    st.header("🛠️ Reset Password & Migrasi Data Pengguna (Akses Admin)")
    st.markdown("---")

    st.subheader("1. Reset Password Pengguna Individual")
    
    user_list_reset = st.session_state.data['name'].tolist()
    user_to_reset_name = st.selectbox(
        "Pilih Pengguna untuk Reset Password:", 
        [''] + sorted([name for name in user_list_reset if name.lower() != ADMIN_USER.lower()]), 
        key="reset_user_select"
    )

    if user_to_reset_name:
        with st.form("reset_password_form", clear_on_submit=True):
            st.info(f"Anda akan mereset password untuk **{user_to_reset_name}**.")
            
            new_pass_admin = st.text_input(
                "Masukkan Password BARU", 
                type="password", 
                key="new_pass_admin_input"
            ).strip()
            
            confirm_pass_admin = st.text_input(
                "Konfirmasi Password BARU", 
                type="password", 
                key="confirm_pass_admin_input"
            ).strip()
            
            reset_button = st.form_submit_button("Lakukan Reset Password")

            if reset_button:
                if not new_pass_admin or not confirm_pass_admin:
                    st.error("Semua kolom password harus diisi.")
                elif new_pass_admin != confirm_pass_admin:
                    st.error("Password baru dan konfirmasi tidak cocok!")
                else:
                    try:
                        user_rows_to_update = st.session_state.data[
                            st.session_state.data['name'] == user_to_reset_name
                        ]
                        
                        if not user_rows_to_update.empty:
                            barcode_id_to_update = user_rows_to_update.index[0]
                            
                            hashed_password_new = hash_password(new_pass_admin)
                            
                            st.session_state.data.loc[barcode_id_to_update, 'password'] = hashed_password_new
                            
                            save_data(st.session_state.data, DATA_FILE)
                            
                            st.success(f"✅ Password untuk **{user_to_reset_name}** berhasil direset!")
                            st.warning("Penting: Berikan password baru ini kepada pengguna dan sarankan mereka untuk login dan menggantinya.")
                            st.rerun() 
                        else:
                            st.error("Pengguna tidak ditemukan dalam database.")

                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat mereset password: {e}")
    
    st.markdown("---")
    
    st.subheader("2. ⚠️ Migrasi Data Password Lama (Lakukan Sekali!)")
    st.info("Gunakan ini jika pengguna lama tidak bisa login. Ini akan mengamankan password mereka dengan Bcrypt.")

    if st.button("Konversi Semua Password Lama ke Format Bcrypt"):
        df = st.session_state.data.copy()
        passwords_migrated = 0
        
        for index, row in df.iterrows():
            plain_password = str(row['password']).strip()
            
            if len(plain_password) < 50 or not plain_password.startswith('$'): 
                
                if plain_password and plain_password.lower() != 'nan':
                    try:
                        hashed = hash_password(plain_password)
                        df.loc[index, 'password'] = hashed
                        passwords_migrated += 1
                    except Exception as e:
                        st.warning(f"Gagal meng-hash password untuk pengguna {row['name']}: {e}")
        
        if passwords_migrated > 0:
            st.session_state.data = df
            save_data(st.session_state.data, DATA_FILE)
            st.success(f"✅ Migrasi berhasil! **{passwords_migrated}** password lama telah di-hash dengan bcrypt.")
            st.balloons()
            st.rerun()
        else:
            st.info("Semua password sudah dalam format bcrypt atau kosong. Tidak ada yang perlu dimigrasi.")

# ----------------- DASHBOARD ANALITIK & GRAFIK ADMIN -----------------
elif st.session_state.app_mode == 'admin_analytics' and st.session_state.user_role == 'admin':
    st.header("Analitik Parkir: Log & Grafik")
    
    if st.session_state.log.empty:
        st.warning("Belum ada data transaksi yang tercatat untuk dianalisis.")
        st.stop()

    df_log = st.session_state.log.copy()
    
    df_log['timestamp'] = pd.to_datetime(df_log['timestamp'], errors='coerce')
    df_log.dropna(subset=['timestamp'], inplace=True)
    
    user_names = ['Semua Pengguna'] + sorted(df_log['name'].unique().tolist())
    selected_name = st.selectbox("Filter berdasarkan Pengguna:", user_names)

    if selected_name != 'Semua Pengguna':
        df_log_filtered = df_log[df_log['name'] == selected_name]
    else:
        df_log_filtered = df_log
        
    st.markdown("---")
    
    # GRAFIK 1: Trend Transaksi Harian
    st.subheader("Grafik 1: Trend Transaksi Masuk/Keluar Harian")
    
    df_log_daily = df_log_filtered.copy()
    df_log_daily['date'] = df_log_daily['timestamp'].dt.date
    
    df_daily_counts = df_log_daily.groupby(['date', 'event_type']).size().reset_index(name='count')

    if not df_daily_counts.empty:
        chart1 = alt.Chart(df_daily_counts).mark_bar().encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('count:Q', title='Jumlah Transaksi'),
            color=alt.Color('event_type:N', title='Tipe Transaksi', scale=alt.Scale(domain=['IN', 'OUT'], range=['#4CAF50', '#FF9800'])),
            tooltip=['date', 'event_type', 'count']
        ).properties(
            title='Jumlah Transaksi Masuk dan Keluar per Hari'
        ).interactive()
        st.altair_chart(chart1, use_container_width=True)
    else:
        st.info("Tidak ada data transaksi harian yang sesuai filter.")

    st.markdown("---")

    # GRAFIK 2: Distribusi Transaksi per Jam
    st.subheader("Grafik 2: Distribusi Transaksi per Jam (Tren Jam Sibuk)")
    
    df_log_hourly = df_log_filtered.copy()
    df_log_hourly['hour'] = df_log_hourly['timestamp'].dt.hour
    
    df_hourly_counts = df_log_hourly.groupby('hour').size().reset_index(name='count')
    df_hourly_counts['hour_label'] = df_hourly_counts['hour'].apply(lambda x: f"{x:02d}:00")

    if not df_hourly_counts.empty:
        chart2 = alt.Chart(df_hourly_counts).mark_line(point=True).encode(
            x=alt.X('hour_label:N', title='Jam (Waktu Lokal)'),
            y=alt.Y('count:Q', title='Jumlah Transaksi'),
            tooltip=['hour_label', 'count']
        ).properties(
            title='Total Transaksi Berdasarkan Jam'
        ).interactive()
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("Tidak ada data transaksi per jam yang sesuai filter.")
    
    st.markdown("---")
    
    # GRAFIK 3: Status Parkir Berdasarkan Jenis Kendaraan
    st.subheader("Grafik 3: Status Parkir Berdasarkan Jenis Kendaraan (Saat Ini)")
    
    df_status = st.session_state.data.copy()
    df_status_counts = df_status.groupby(['vehicle_type', 'status']).size().reset_index(name='count')

    if not df_status_counts.empty:
        chart3 = alt.Chart(df_status_counts).mark_bar().encode(
            x=alt.X('vehicle_type:N', title='Jenis Kendaraan'),
            y=alt.Y('count:Q', title='Jumlah Kendaraan'),
            color=alt.Color('status:N', title='Status', scale=alt.Scale(domain=['IN', 'OUT'], range=['#4CAF50', '#F44336'])),
            column=alt.Column('status:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
            tooltip=['vehicle_type', 'status', 'count']
        ).properties(
            title='Status Parkir Saat Ini'
        ).interactive()
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.info("Tidak ada data status parkir.")

    st.markdown("---")
    st.subheader("Tabel Log Transaksi Terakhir")
    st.dataframe(df_log_filtered.tail(100).sort_values(by='timestamp', ascending=False), use_container_width=True)















