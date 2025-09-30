import streamlit as st
import pandas as pd
import uuid
import qrcode
from io import BytesIO
import os
from datetime import datetime

# --- KONFIGURASI APLIKASI ---
DATA_FILE = 'parking_users.csv'
ADMIN_USER = "petugas"         
ADMIN_PASS = "admin123"        

# Kolom yang wajib ada di dalam DataFrame/CSV (DITAMBAH: time_in, time_out, duration)
REQUIRED_COLUMNS = ['barcode_id', 'name', 'user_id', 'vehicle_type', 'license_plate', 'password', 'status', 'time_in', 'time_out', 'duration']

# --- FUNGSI PEMBANTU (UTILITIES) ---

def load_data():
    """Memuat data dari CSV atau membuat DataFrame baru, dan memastikan semua kolom penting ada."""
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        # LOGIKA PERBAIKAN KOLOM HILANG
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = '' 
        
        # PERBAIKAN TIPE DATA UTAMA
        df['user_id'] = df['user_id'].astype(str) 
        df['name'] = df['name'].astype(str) 
        
        # KONVERSI TIPE DATA WAKTU
        # Konversi kolom waktu ke datetime, error='coerce' akan mengubah data rusak menjadi NaT (Not a Time)
        df['time_in'] = pd.to_datetime(df['time_in'], errors='coerce')
        df['time_out'] = pd.to_datetime(df['time_out'], errors='coerce')
        
    else:
        # Buat DataFrame kosong jika file belum ada
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    # Pastikan index diatur ke barcode_id
    df = df.set_index('barcode_id', drop=False)
    return df

def save_data(df):
    """Menyimpan DataFrame ke CSV."""
    df.to_csv(DATA_FILE, index=False)

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

# --- INISIALISASI APLIKASI DAN SESSION STATE ---
st.set_page_config(layout="wide", page_title="Dashboard Parkir Barcode")

# Muat data ke Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Mengatur status aplikasi (Mode)
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'login'
if 'logged_in_user_id' not in st.session_state:
    st.session_state.logged_in_user_id = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None 

# Tombol Logout (Selalu di atas, kecuali di mode login/register)
if st.session_state.app_mode not in ['login', 'register']:
    if st.button("Logout"):
        st.session_state.app_mode = 'login'
        st.session_state.logged_in_user_id = None
        st.session_state.user_role = None
        st.rerun() 

st.title("🅿️ Aplikasi Dashboard Parkir Barcode")
st.markdown("---")


# =================================================================
# FUNGSI APLIKASI BERDASARKAN MODE
# =================================================================

# ----------------- MODE LOGIN / REGISTER -----------------
if st.session_state.app_mode == 'login':
    st.subheader("Selamat Datang! Silakan Login atau Daftar")
    col_l, col_r = st.columns(2)

    with col_l:
        with st.form("login_form"):
            st.write("### Login Pengguna/Petugas")
            
            # PERUBAHAN: Input menggunakan Nama Lengkap
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

                # 2. Cek login Pengguna Biasa (Berdasarkan Nama Lengkap)
                else:
                    found_user = st.session_state.data[
                        st.session_state.data['name'].str.lower() == login_name_or_admin.lower()
                    ]

                    if not found_user.empty:
                        first_match = found_user.iloc[0]

                        # Cek password
                        if first_match['password'] == login_pass: 
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


# ----------------- MODE REGISTER -----------------
elif st.session_state.app_mode == 'register':
    st.subheader("Buat Akun Parkir Baru")
    
    if st.button("<< Kembali ke Login"):
        st.session_state.app_mode = 'login'
        st.rerun()
        
    with st.form("register_form"):
        name = st.text_input("Nama Lengkap", key="reg_name")
        user_id = st.text_input("NIM/NIP (Ini adalah ID Unik Anda)", key="reg_user_id")
        password = st.text_input("Buat Password", type="password", key="reg_pass")
        vehicle_type = st.selectbox("Jenis Kendaraan", ['Motor', 'Mobil'], key="reg_vehicle")
        license_plate = st.text_input("Nomor Polisi (Nopol)", key="reg_nopol").upper()
        
        submitted = st.form_submit_button("Daftar & Buat Barcode Pertama")

        if submitted:
            if name and user_id and password and license_plate:
                if user_id in st.session_state.data['user_id'].values:
                    st.error("NIM/NIP ini sudah terdaftar. Silakan Login.")
                else:
                    new_barcode_id = str(uuid.uuid4())
                    new_data = {
                        'barcode_id': new_barcode_id,
                        'name': name,
                        'user_id': user_id,
                        'password': password, 
                        'vehicle_type': vehicle_type,
                        'license_plate': license_plate,
                        'status': 'OUT',
                        'time_in': pd.NaT, # Not a Time (Kosong)
                        'time_out': pd.NaT, # Kosong
                        'duration': '' # Kosong
                    }
                    st.session_state.data.loc[new_barcode_id] = new_data
                    save_data(st.session_state.data)
                    
                    st.success("Pendaftaran berhasil! Silakan Login.")
                    st.session_state.app_mode = 'login' 
                    st.rerun() 
            else:
                st.error("Semua kolom harus diisi!")


# ----------------- DASHBOARD PENGGUNA -----------------
elif st.session_state.app_mode == 'user_dashboard' and st.session_state.user_role == 'user':
    user_id = st.session_state.logged_in_user_id
    user_data = st.session_state.data.loc[user_id]
    
    st.header(f"Selamat Datang di Dashboard Anda, {user_data['name']}!")
    
    col_info, col_qr = st.columns([1, 1])
    
    with col_info:
        st.subheader("Identitas dan Data Kendaraan")
        st.markdown(f"**Nama Lengkap:** {user_data['name']}")
        st.markdown(f"**NIM/NIP:** {user_data['user_id']}")
        st.markdown(f"**Jenis Kendaraan:** {user_data['vehicle_type']}")
        st.markdown(f"**Nomor Polisi:** {user_data['license_plate']}")
        st.markdown(f"**Status Parkir Saat Ini:** **{user_data['status']}**")
        
        # Tampilkan data waktu
        st.markdown("---")
        st.subheader("Informasi Waktu")
        
        # Cek apakah ada data waktu masuk yang valid
        if pd.notna(user_data['time_in']):
            st.markdown(f"**Waktu Masuk:** {user_data['time_in'].strftime('%d %b %Y, %H:%M:%S')}")
        else:
            st.markdown(f"**Waktu Masuk:** Belum ada data masuk.")
            
        # Cek apakah ada data durasi (hanya muncul setelah keluar)
        if user_data['status'] == 'OUT' and user_data['duration']:
            st.markdown(f"**Waktu Keluar:** {user_data['time_out'].strftime('%d %b %Y, %H:%M:%S')}")
            st.success(f"**Durasi Parkir:** {user_data['duration']}")

    with col_qr:
        st.subheader("Barcode Akses Parkir (Kunci Gerbang)")
        st.info("Tunjukkan Barcode ini ke scanner di gerbang untuk masuk/keluar.")
        
        qr_buffer = generate_qr_code(user_id)
        st.image(qr_buffer, caption=f"ID: {user_id[:8]}...", width=250)
        
        st.download_button(
            label="Download Barcode (PNG)",
            data=qr_buffer,
            file_name=f"{user_data['name']}_parkir.png",
            mime="image/png"
        )


# ----------------- DASHBOARD ADMIN/PETUGAS -----------------
elif st.session_state.app_mode == 'admin_dashboard' and st.session_state.user_role == 'admin':
    st.header("Dashboard Petugas Parkir (Akses Admin)")
    
    col_scan, col_stats = st.columns([1, 1])

    with col_scan:
        st.subheader("Simulasi Scanner Gerbang")
        scan_id = st.text_input("Masukkan Barcode ID (Salin dari Dashboard Pengguna):").strip()
        scan_button = st.button("PROSES SCAN & BUKA GERBANG")
        
        if scan_button and scan_id:
            if scan_id in st.session_state.data.index:
                
                # --- LOGIKA PENCATATAN WAKTU ---
                
                user_row = st.session_state.data.loc[scan_id]
                current_status = user_row['status']
                current_time = datetime.now()
                name = user_row['name']
                
                # Logika Pintu Masuk/Keluar
                if current_status == 'OUT':
                    # Aksi MASUK
                    new_status = 'IN'
                    action = "MASUK"
                    
                    st.session_state.data.loc[scan_id, 'status'] = new_status
                    st.session_state.data.loc[scan_id, 'time_in'] = current_time # Catat Waktu Masuk
                    st.session_state.data.loc[scan_id, 'time_out'] = pd.NaT      # Reset Waktu Keluar
                    st.session_state.data.loc[scan_id, 'duration'] = ''          # Reset Durasi
                    
                    save_data(st.session_state.data)
                    st.success(f"✅ GERBANG TERBUKA! Selamat {action}, {name}. Status baru: DI DALAM.")
                    
                else: # Status is 'IN'
                    # Aksi KELUAR
                    new_status = 'OUT'
                    action = "KELUAR"
                    
                    time_in = st.session_state.data.loc[scan_id, 'time_in']
                    
                    if pd.notna(time_in):
                        duration = current_time - time_in
                        # Format durasi ke jam:menit:detik
                        duration_str = str(duration).split('.')[0] 
                    else:
                        duration_str = "0:00:00 (Error Waktu Masuk)"
                    
                    st.session_state.data.loc[scan_id, 'status'] = new_status
                    st.session_state.data.loc[scan_id, 'time_out'] = current_time # Catat Waktu Keluar
                    st.session_state.data.loc[scan_id, 'duration'] = duration_str # Catat Durasi
                    
                    save_data(st.session_state.data)
                    st.info(f"🚪 GERBANG TERBUKA! Selamat {action}, {name}. Durasi Parkir: {duration_str}. Status baru: DI LUAR.")
                
                st.rerun()
            else:
                st.error("❌ Barcode ID tidak terdaftar!")

    # Statistik Dashboard
    with col_stats:
        st.subheader("Ringkasan Status")
        total_users = len(st.session_state.data)
        parked_count = len(st.session_state.data[st.session_state.data['status'] == 'IN'])
        out_count = total_users - parked_count

        col_met1, col_met2, col_met3 = st.columns(3)
        col_met1.metric(label="Total Pengguna Terdaftar", value=total_users)
        col_met2.metric(label="Sedang Parkir (IN)", value=parked_count)
        col_met3.metric(label="Sudah Keluar (OUT)", value=out_count)

    st.markdown("---")
    
    # Tabel Status Parkir
    st.subheader("Tabel Status Parkir Saat Ini")
    # Tambahkan kolom waktu dan durasi untuk ditampilkan
    display_data = st.session_state.data[['name', 'user_id', 'license_plate', 'status', 'time_in', 'time_out', 'duration']].copy()
    
    # Format kolom waktu agar mudah dibaca sebelum ditampilkan
    display_data['time_in'] = display_data['time_in'].dt.strftime('%H:%M:%S, %d/%m').fillna('-')
    display_data['time_out'] = display_data['time_out'].dt.strftime('%H:%M:%S, %d/%m').fillna('-')

    def color_status(val):
        color = 'lightgreen' if val == 'IN' else 'salmon'
        return f'background-color: {color}'

    st.dataframe(
        display_data.style.applymap(color_status, subset=['status']),
        use_container_width=True
    )
    
    # --- LOGIKA PENGHAPUSAN AKUN OLEH ADMIN ---
    st.markdown("---")
    st.subheader("Opsi Admin: Hapus Akun Pengguna")
    
    # Tampilkan daftar pengguna untuk dipilih
    user_list = st.session_state.data['name'].tolist()
    
    # Tambahkan opsi kosong untuk menghindari penghapusan tidak sengaja
    user_to_delete_name = st.selectbox("Pilih Pengguna yang akan dihapus:", [''] + user_list)
    
    delete_button = st.button("Hapus Akun Pengguna Terpilih", disabled=(user_to_delete_name == ''))
    
    if delete_button and user_to_delete_name:
        # Temukan barcode_id berdasarkan nama yang dipilih
        try:
            # Cari baris pertama yang cocok dengan nama
            user_row_to_delete = st.session_state.data[st.session_state.data['name'] == user_to_delete_name].iloc[0]
            barcode_id_to_delete = user_row_to_delete.name
            
            # Hapus baris dari DataFrame
            st.session_state.data.drop(index=barcode_id_to_delete, inplace=True)
            save_data(st.session_state.data)
            
            st.success(f"Akun pengguna {user_to_delete_name} berhasil dihapus. Akun ini tidak dapat digunakan lagi.")
            st.rerun()
            
        except IndexError:
            st.error("Pengguna tidak ditemukan atau terjadi masalah saat penghapusan.")
