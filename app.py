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
import base64 

# --- KONFIGURASI APLIKASI ---
DATA_FILE = 'parking_users.csv'
LOG_FILE = 'parking_log.csv'

# Memuat kredensial dari st.secrets.
try:
    ADMIN_USER = st.secrets.admin.username
    ADMIN_PASS = st.secrets.secrets_pass.password
    
except:
    # Default credentials for local testing if secrets.toml is not available
    ADMIN_USER = "petugas" 
    ADMIN_PASS = "12345"
    
MONITOR_TIMEOUT_SECONDS = 5 # Durasi tampil pesan sukses di monitor (5 detik)

REQUIRED_USER_COLUMNS = ['barcode_id', 'name', 'user_id', 'vehicle_type', 'license_plate', 'password', 'status', 'time_in', 'time_out', 'duration']
REQUIRED_LOG_COLUMNS = ['event_id', 'barcode_id', 'name', 'timestamp', 'event_type']


# -----------------------------------------------------------------------------
# >>> FUNGSI UNTUK LATAR BELAKANG (BASE64 & BURAM) <<<
# -----------------------------------------------------------------------------

def get_base64_of_bin_file(bin_file):
    """Membaca file dan mengkonversinya menjadi Base64 string."""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError: 
        print(f"Error: File gambar '{bin_file}' tidak ditemukan.")
        return None

def set_background(image_path):
    """Menyuntikkan CSS untuk mengatur gambar latar belakang buram."""
    
    base64_img = get_base64_of_bin_file(image_path)
    
    if base64_img is not None:
        st.markdown(
            f"""
            <style>
            /* 1. LAPISAN LATAR BELAKANG DENGAN GAMBAR BURAM (Menggunakan ::before) */
            .stApp::before {{
                content: "";
                position: fixed; /* Membuatnya tetap di tempat saat scroll */
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: url("data:image/jpeg;base64,{base64_img}");
                background-size: cover; 
                background-attachment: fixed; 
                background-position: center;
                
                /* >>> INI YANG MEMBUAT GAMBAR GEDUNG (LATAR BELAKANG) BURAM <<< */
                filter: blur(5px); /* Nilai blur: 5px */
                -webkit-filter: blur(5px); 
                
                z-index: -1; /* Pindahkan ke belakang semua elemen Streamlit */
            }}

            /* 2. Sidebar dengan latar belakang semi-transparan (tidak blur) */
            [data-testid="stSidebar"] {{
                background-color: rgba(255, 255, 255, 0.8); 
                border-right: 1px solid #ccc;
            }}

            /* 3. Konten utama (kotak dashboard/block-container) dengan latar belakang semi-transparan */
            /* Ini menargetkan kontainer yang memuat semua widget. */
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.9); /* Latar konten semi transparan */
                border-radius: 10px; 
                padding: 10px 20px 20px 20px; 
            }}
            
            /* 4. Teks Berbayangan agar tetap terbaca di atas buram */
            h1, h2, h3, p, .stMarkdown, .css-1d3f9b, .css-1dp5vir, label, button, .st-df, .st-ck {{
                color: #333333; 
                text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.7); 
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"File '{image_path}' tidak ditemukan. Latar belakang default (putih) digunakan.")
        
# -----------------------------------------------------------------------------
# >>> FUNGSI UNTUK LATAR BELAKANG SELESAI DI SINI <<<
# -----------------------------------------------------------------------------


# --- FUNGSI UTAMA (DEFAULT MONITOR MESSAGE) ---

def get_default_monitor_message():
    """Mengembalikan HTML untuk pesan monitor default (Scan Here)."""
    return (
        f"<div style='background-color: #f1f3f5; color: #495057; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"
        f"<h1 style='margin: 0; font-size: 80px;'>SCAN BARCODE ANDA</h1>"
        f"<p style='font-size: 30px;'>Arahkan Barcode ke Kamera/Scanner</p>"
        f"<div style='width: 250px; height: 150px; border: 10px solid #495057; margin: 20px auto; border-radius: 10px;'></div>" 
        f"</div>"
    )

# --- FUNGSI PEMBANTU (UTILITIES) ---

def hash_password(password):
    """Menghasilkan hash dari password menggunakan bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password, hashed_password):
    """Memverifikasi password yang dimasukkan dengan hash yang tersimpan."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False
        
def load_data(file_name, required_cols):
    """Memuat data dari CSV atau membuat DataFrame baru, dan memastikan semua kolom penting ada."""
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' 
        
        for col in ['user_id', 'name', 'password']:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('')
            
        for col in ['timestamp', 'time_in', 'time_out']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
        if 'barcode_id' in df.columns:
            df = df.set_index('barcode_id', drop=False)
            
    else:
        df = pd.DataFrame(columns=required_cols)
        if 'barcode_id' in required_cols:
            df.set_index('barcode_id', drop=False, inplace=True)
    
    return df

def save_data(df, file_name):
    """Menyimpan DataFrame ke CSV."""
    df.to_csv(file_name, index=False)

def generate_qr_code(data):
    """Menghasilkan gambar QR code (Barcode) di memori."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def add_to_log(barcode_id, name, event_type, timestamp):
    """Menambahkan entri baru ke tabel log."""
    new_log = {
        'event_id': str(uuid.uuid4()),
        'barcode_id': barcode_id,
        'name': name,
        'timestamp': timestamp,
        'event_type': event_type
    }
    # Menggunakan pd.concat untuk menambah baris
    new_log_df = pd.DataFrame([new_log], columns=st.session_state.log.columns)
    st.session_state.log = pd.concat([st.session_state.log, new_log_df], ignore_index=True)
    save_data(st.session_state.log, LOG_FILE)

def set_monitor_message(html_content, type='default'):
    """Menyimpan pesan HTML untuk ditampilkan di Gate Monitor dan mereset timer."""
    st.session_state.monitor_html = html_content
    st.session_state.monitor_type = type
    st.session_state.monitor_display_time = datetime.now() 

def process_scan(scan_id, feedback_placeholder):
    """
    Logika utama untuk memproses ID Barcode yang diterima.
    Fungsi ini akan mengatur pesan monitor.
    """
    
    # Check 1: ID Barcode kosong atau simulasi
    if not scan_id or scan_id in ["simulasi1234", "simulasi_camera_id_12345"]: 
        feedback_placeholder.error("ID Barcode kosong atau tidak valid.")
        set_monitor_message(
            f"<div style='background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
            f"<h1 style='margin: 0; font-size: 80px;'>❌ ERROR!</h1>"\
            f"<p style='font-size: 40px; font-weight: bold;'>BARCODE TIDAK VALID / KOSONG</p>"\
            f"</div>", 'ERROR'
        )
        # PENTING: Paksakan transisi ke Monitor
        st.session_state.app_mode = 'gate_monitor'
        return 

        
    # Check 2: ID Barcode terdaftar
    if scan_id in st.session_state.data.index:
        user_row = st.session_state.data.loc[scan_id]
        current_status = user_row['status']
        current_time = datetime.now()
        name = user_row['name']
        license_plate = user_row['license_plate']
        
        # Logika Pintu Masuk/Keluar
        if current_status == 'OUT':
            # Aksi MASUK
            st.session_state.data.loc[scan_id, 'status'] = 'IN'
            st.session_state.data.loc[scan_id, 'time_in'] = current_time 
            st.session_state.data.loc[scan_id, 'time_out'] = pd.NaT       
            st.session_state.data.loc[scan_id, 'duration'] = ''           
            save_data(st.session_state.data, DATA_FILE)
            add_to_log(scan_id, name, 'IN', current_time)

            # Update Monitor (Pesan Selamat Datang)
            set_monitor_message(
                f"<div style='background-color: #d4edda; color: #155724; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
                f"<h1 style='margin: 0; font-size: 80px;'>✅ SELAMAT DATANG!</h1>"\
                f"<p style='margin-top: 20px; font-size: 50px; font-weight: bold;'>{name}</p>"\
                f"<p style='font-size: 40px;'>({license_plate})</p>"\
                f"</div>", 'IN'
            )
            feedback_placeholder.success(f"GERBANG TERBUKA! {name} masuk.")
            
        else: # Status is 'IN'
            # Aksi KELUAR
            time_in = st.session_state.data.loc[scan_id, 'time_in']
            
            if pd.notna(time_in) and isinstance(time_in, datetime):
                duration = current_time - time_in
                duration_str = str(duration).split('.')[0] 
            else:
                duration_str = "0:00:00 (Error Waktu Masuk)"
            
            st.session_state.data.loc[scan_id, 'status'] = 'OUT'
            st.session_state.data.loc[scan_id, 'time_out'] = current_time 
            st.session_state.data.loc[scan_id, 'duration'] = duration_str 
            save_data(st.session_state.data, DATA_FILE)
            add_to_log(scan_id, name, 'OUT', current_time)

            # Update Monitor (Pesan Sampai Jumpa)
            set_monitor_message(
                f"<div style='background-color: #fff3cd; color: #856404; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
                f"<h1 style='margin: 0; font-size: 80px;'>🚪 SAMPAI JUMPA LAGI</h1>"\
                f"<p style='margin-top: 20px; font-size: 50px; font-weight: bold;'>{name}</p>"\
                f"<p style='font-size: 40px;'>({license_plate})</p>"\
                f"<p style='font-size: 25px;'>Durasi Parkir: {duration_str}</p>"\
                f"</div>", 'OUT'
            )
            feedback_placeholder.info(f"GERBANG TERBUKA! {name} keluar. Durasi: {duration_str}")
        
        # PENTING: Paksakan transisi ke Monitor setelah status berhasil diubah
        st.session_state.app_mode = 'gate_monitor'
        return 

    else:
        # Pesan Barcode Tidak Terdaftar
        set_monitor_message(
            f"<div style='background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; text-align: center; height: 100vh; display: flex; flex-direction: column; justify-content: center;'>"\
            f"<h1 style='margin: 0; font-size: 80px;'>❌ ERROR!</h1>"\
            f"<p style='font-size: 40px; font-weight: bold;'>BARCODE TIDAK TERDAFTAR</p>"\
            f"</div>", 'ERROR'
        )
        feedback_placeholder.error("❌ Barcode ID tidak terdaftar!")
        # PENTING: Paksakan transisi ke Monitor
        st.session_state.app_mode = 'gate_monitor'
        return


# --- INISIALISASI APLIKASI DAN SESSION STATE ---
st.set_page_config(layout="wide", page_title="Dashboard Parkir Barcode")

# -----------------------------------------------------------------------------
# >>> PEMANGGILAN FUNGSI LATAR BELAKANG DITAMBAHKAN DI SINI <<<
set_background('BG-FASILKOM.jpeg') 
# -----------------------------------------------------------------------------

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
    
# --- INISIALISASI MONITOR STATE ---
if 'monitor_html' not in st.session_state:
    st.session_state.monitor_html = get_default_monitor_message()  
    
if 'monitor_type' not in st.session_state:     
    st.session_state.monitor_type = 'default'   

if 'monitor_display_time' not in st.session_state:
    st.session_state.monitor_display_time = datetime.now() - timedelta(seconds=MONITOR_TIMEOUT_SECONDS + 1)
    
if 'admin_table_filter' not in st.session_state:
    st.session_state.admin_table_filter = 'ALL' 
    
# Tombol Logout dan Menu Admin/Monitor
st.sidebar.title("Menu Aplikasi")

if st.session_state.app_mode == 'gate_monitor':
    st.sidebar.markdown("*Monitor Sedang Aktif*")
    if st.sidebar.button("Kembali ke Dashboard Admin"):
        st.session_state.app_mode = 'admin_dashboard'
        st.rerun()
elif st.session_state.app_mode not in ['login', 'register']:
    if st.session_state.user_role == 'admin':
        if st.sidebar.button("Dashboard Petugas"):
            st.session_state.app_mode = 'admin_dashboard'
            st.rerun()
        if st.sidebar.button("Analitik & Grafik"):
            st.session_state.app_mode = 'admin_analytics'
            st.rerun()
        if st.sidebar.button("Reset Password Pengguna"):
            st.session_state.app_mode = 'admin_reset_password'
            st.rerun()
        st.sidebar.markdown("---")
        if st.sidebar.button("Buka Monitor Gerbang"):
             st.session_state.app_mode = 'gate_monitor'
             st.rerun()
        st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):
        st.session_state.app_mode = 'login'
        st.session_state.logged_in_user_id = None
        st.session_state.user_role = None
        st.rerun()    

if st.session_state.app_mode != 'gate_monitor':
    st.title("🅿 Dashboard Parkir")
    st.markdown("---")

# =================================================================
# FUNGSI APLIKASI BERDASARKAN MODE
# =================================================================

# ----------------- MODE MONITOR GERBANG (Logika Timer Stabil) -----------------
if st.session_state.app_mode == 'gate_monitor':
    
    # Hitung waktu yang berlalu sejak pesan terakhir ditampilkan
    time_elapsed = datetime.now() - st.session_state.monitor_display_time
    
    # Cek apakah waktu sudah melewati batas timeout (5 detik)
    if st.session_state.monitor_type != 'default' and time_elapsed.total_seconds() >= MONITOR_TIMEOUT_SECONDS:
        
        # 1. Reset pesan ke default
        st.session_state.monitor_html = get_default_monitor_message()
        st.session_state.monitor_type = 'default'
        
        # 2. Reset display time ke waktu lampau agar tidak terjadi loop reset
        st.session_state.monitor_display_time = datetime.now() - timedelta(seconds=MONITOR_TIMEOUT_SECONDS + 1)
        
        # 3. PENTING: Paksa RERUN untuk menampilkan pesan default
        st.rerun() 
        
    # Tampilkan pesan monitor
    st.markdown(
        st.session_state.monitor_html, 
        unsafe_allow_html=True
    )
    
    # Logika RERUN Otomatis untuk menghitung mundur
    if st.session_state.monitor_type != 'default' and time_elapsed.total_seconds() < MONITOR_TIMEOUT_SECONDS:
        
        # Tampilkan hitungan mundur 
        time_left = MONITOR_TIMEOUT_SECONDS - int(time_elapsed.total_seconds())
        st.empty().markdown(
            f"<div style='text-align: right; color: gray;'>⏳ Kembali dalam {time_left} detik...</div>", 
            unsafe_allow_html=True
        )
        
        # Tunggu 1 detik
        time.sleep(1) 
        
        # PENTING: Paksa Streamlit untuk menjalankan ulang skrip agar cek waktu berikutnya
        st.rerun() 
    
    st.stop() 

# ----------------- MODE LOGIN / REGISTER / USER DASHBOARD -----------------
elif st.session_state.app_mode == 'login':
    st.subheader("Selamat Datang! Silakan Login atau Daftar")
    col_l, col_r = st.columns(2)

    with col_l:
        with st.form("login_form"):
            st.write("### Login Pengguna/Petugas")
            
            login_name_or_admin = st.text_input("Nama Lengkap Anda (atau 'petugas')", key="login_id").strip()
            login_pass = st.text_input("Password", type="password", key="login_pass")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                
                # 1. Cek login Admin
                if login_name_or_admin == ADMIN_USER and login_pass == ADMIN_PASS:
                    st.session_state.app_mode = 'admin_dashboard'
                    st.session_state.user_role = 'admin'
                    st.success("Login sebagai Petugas/Admin berhasil!")
                    st.rerun()

                # 2. Cek login Pengguna Biasa
                else:
                    found_user = st.session_state.data[
                        st.session_state.data['name'].str.lower() == login_name_or_admin.lower()
                    ]

                    if not found_user.empty:
                        first_match = found_user.iloc[0]

                        stored_password_clean = str(first_match['password']).strip()
                        
                        if stored_password_clean and check_password(login_pass, stored_password_clean):
                            st.session_state.app_mode = 'user_dashboard'
                            st.session_state.user_role = 'user'
                            st.session_state.logged_in_user_id = first_match['barcode_id'] 
                            st.success(f"Login pengguna {first_match['name']} berhasil!")
                            st.rerun()
                        else:
                            st.error("Password salah!") 
                    else:
                        st.error("Nama Lengkap tidak terdaftar!")


    with col_r:
        if st.button("Daftar Akun Baru (Register)"):
            st.session_state.app_mode = 'register'
            st.rerun()


elif st.session_state.app_mode == 'register':
    st.subheader("Buat Akun Parkir Baru")
    
    if st.button("<< Kembali ke Login"):
        st.session_state.app_mode = 'login'
        st.rerun()
        
    with st.form("register_form"):
        name = st.text_input("Nama Lengkap", key="reg_name").strip()
        user_id = st.text_input("NIM/NIP (Ini adalah ID Unik Anda)", key="reg_user_id").strip()
        password = st.text_input("Buat Password", type="password", key="reg_pass").strip()
        vehicle_type = st.selectbox("Jenis Kendaraan", ['Motor', 'Mobil'], key="reg_vehicle")
        license_plate = st.text_input("Nomor Polisi (Nopol)", key="reg_nopol").upper().strip()
        
        submitted = st.form_submit_button("Daftar & Buat Barcode Pertama")

        if submitted:
            if name and user_id and password and license_plate:
                if user_id in st.session_state.data['user_id'].values:
