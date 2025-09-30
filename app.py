import streamlit as st
import pandas as pd
import uuid
import qrcode
from io import BytesIO
import os
from datetime import datetime, timedelta
import altair as alt

# --- KONFIGURASI APLIKASI ---
DATA_FILE = 'parking_users.csv'
LOG_FILE = 'parking_log.csv' 
ADMIN_USER = "petugas"         
ADMIN_PASS = "admin123"        

REQUIRED_USER_COLUMNS = ['barcode_id', 'name', 'user_id', 'vehicle_type', 'license_plate', 'password', 'status', 'time_in', 'time_out', 'duration']
REQUIRED_LOG_COLUMNS = ['event_id', 'barcode_id', 'name', 'timestamp', 'event_type']

# --- FUNGSI PEMBANTU (UTILITIES) ---

def load_data(file_name, required_cols):
    """Memuat data dari CSV atau membuat DataFrame baru, dan memastikan semua kolom penting ada."""
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        
        # LOGIKA PERBAIKAN KOLOM HILANG
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' 
        
        # PERBAIKAN TIPE DATA UTAMA
        if 'user_id' in df.columns:
            df['user_id'] = df['user_id'].astype(str)
        if 'name' in df.columns:
            df['name'] = df['name'].astype(str)
            
        # PERBAIKAN BARU: Pastikan password adalah string dan isi NaN dengan string kosong
        if 'password' in df.columns:
            df['password'] = df['password'].astype(str).fillna('')
            
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        if 'time_in' in df.columns:
            df['time_in'] = pd.to_datetime(df['time_in'], errors='coerce')
        if 'time_out' in df.columns:
            df['time_out'] = pd.to_datetime(df['time_out'], errors='coerce')
            
    else:
        df = pd.DataFrame(columns=required_cols)
    
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
    st.session_state.log.loc[len(st.session_state.log)] = new_log
    save_data(st.session_state.log, LOG_FILE)


# --- INISIALISASI APLIKASI DAN SESSION STATE ---
st.set_page_config(layout="wide", page_title="Dashboard Parkir Barcode")

# Muat data utama dan log
if 'data' not in st.session_state:
    st.session_state.data = load_data(DATA_FILE, REQUIRED_USER_COLUMNS).set_index('barcode_id', drop=False)
if 'log' not in st.session_state:
    st.session_state.log = load_data(LOG_FILE, REQUIRED_LOG_COLUMNS)

# Mengatur status aplikasi (Mode)
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'login'
if 'logged_in_user_id' not in st.session_state:
    st.session_state.logged_in_user_id = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None 

# Tombol Logout dan Menu Admin
st.sidebar.title("Menu Aplikasi")
if st.session_state.app_mode not in ['login', 'register']:
    if st.session_state.user_role == 'admin':
        if st.sidebar.button("Dashboard Petugas"):
            st.session_state.app_mode = 'admin_dashboard'
            st.rerun()
        if st.sidebar.button("Analitik & Grafik"):
            st.session_state.app_mode = 'admin_analytics'
            st.rerun()
        st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):
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

                        # PERBAIKAN LOGIS: Bersihkan password dari spasi sebelum dibandingkan
                        stored_password_clean = str(first_match['password']).strip()

                        if stored_password_clean == login_pass: 
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
        name = st.text_input("Nama Lengkap", key="reg_name").strip() # Tambahkan strip()
        user_id = st.text_input("NIM/NIP (Ini adalah ID Unik Anda)", key="reg_user_id").strip() # Tambahkan strip()
        password = st.text_input("Buat Password", type="password", key="reg_pass").strip() # Tambahkan strip()
        vehicle_type = st.selectbox("Jenis Kendaraan", ['Motor', 'Mobil'], key="reg_vehicle")
        license_plate = st.text_input("Nomor Polisi (Nopol)", key="reg_nopol").upper().strip() # Tambahkan strip()
        
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
                        'time_in': pd.NaT,
                        'time_out': pd.NaT,
                        'duration': ''
                    }
                    st.session_state.data.loc[new_barcode_id] = new_data
                    save_data(st.session_state.data, DATA_FILE)
                    
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
        
        st.markdown("---")
        st.subheader("Informasi Waktu")
        
        if pd.notna(user_data['time_in']):
            st.markdown(f"**Waktu Masuk:** {user_data['time_in'].strftime('%d %b %Y, %H:%M:%S')}")
        else:
            st.markdown(f"**Waktu Masuk:** Belum ada data masuk.")
            
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
        scan_id = st.text_input("Masukkan Barcode ID:").strip()
        scan_button = st.button("PROSES SCAN & BUKA GERBANG")
        
        if scan_button and scan_id:
            if scan_id in st.session_state.data.index:
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
                    st.session_state.data.loc[scan_id, 'time_in'] = current_time 
                    st.session_state.data.loc[scan_id, 'time_out'] = pd.NaT      
                    st.session_state.data.loc[scan_id, 'duration'] = ''          
                    save_data(st.session_state.data, DATA_FILE)
                    
                    # Tambahkan ke log
                    add_to_log(scan_id, name, 'IN', current_time)

                    st.success(f"✅ GERBANG TERBUKA! Selamat {action}, {name}. Status baru: DI DALAM.")
                    
                else: # Status is 'IN'
                    # Aksi KELUAR
                    new_status = 'OUT'
                    action = "KELUAR"
                    
                    time_in = st.session_state.data.loc[scan_id, 'time_in']
                    
                    if pd.notna(time_in):
                        duration = current_time - time_in
                        duration_str = str(duration).split('.')[0] 
                    else:
                        duration_str = "0:00:00 (Error Waktu Masuk)"
                    
                    st.session_state.data.loc[scan_id, 'status'] = new_status
                    st.session_state.data.loc[scan_id, 'time_out'] = current_time 
                    st.session_state.data.loc[scan_id, 'duration'] = duration_str 
                    save_data(st.session_state.data, DATA_FILE)
                    
                    # Tambahkan ke log
                    add_to_log(scan_id, name, 'OUT', current_time)

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
    
    # Tabel Status Parkir & Hapus Akun
    st.subheader("Tabel Status Parkir Saat Ini")
    display_data = st.session_state.data[['name', 'user_id', 'license_plate', 'status', 'time_in', 'time_out', 'duration']].copy()
    
    display_data['time_in'] = display_data['time_in'].dt.strftime('%H:%M:%S, %d/%m').fillna('-')
    display_data['time_out'] = display_data['time_out'].dt.strftime('%H:%M:%S, %d/%m').fillna('-')

    def color_status(val):
        color = 'lightgreen' if val == 'IN' else 'salmon'
        return f'background-color: {color}'

    st.dataframe(
        display_data.style.applymap(color_status, subset=['status']),
        use_container_width=True
    )
    
    # LOGIKA PENGHAPUSAN AKUN OLEH ADMIN
    st.markdown("---")
    st.subheader("Opsi Admin: Hapus Akun Pengguna")
    
    user_list = st.session_state.data['name'].tolist()
    user_to_delete_name = st.selectbox("Pilih Pengguna yang akan dihapus:", [''] + user_list)
    
    delete_button = st.button("Hapus Akun Pengguna Terpilih", disabled=(user_to_delete_name == ''))
    
    if delete_button and user_to_delete_name:
        try:
            user_rows = st.session_state.data[st.session_state.data['name'] == user_to_delete_name]
            barcode_id_to_delete = user_rows.index.tolist()
            
            st.session_state.data.drop(index=barcode_id_to_delete, inplace=True)
            save_data(st.session_state.data, DATA_FILE)

            st.session_state.log = st.session_state.log[~st.session_state.log['barcode_id'].isin(barcode_id_to_delete)]
            save_data(st.session_state.log, LOG_FILE)
            
            st.success(f"Akun pengguna {user_to_delete_name} (dan {len(barcode_id_to_delete)} data terkait) berhasil dihapus.")
            st.rerun()
            
        except Exception as e:
            st.error(f"Terjadi masalah saat penghapusan: {e}")


# ----------------- DASHBOARD ANALITIK & GRAFIK ADMIN -----------------
elif st.session_state.app_mode == 'admin_analytics' and st.session_state.user_role == 'admin':
    st.header("Analitik Parkir: Log & Grafik")
    
    if st.session_state.log.empty:
        st.warning("Belum ada data transaksi yang tercatat untuk dianalisis.")
        st.stop()

    df_log = st.session_state.log.copy()
    
    # --- Filter Berdasarkan Pengguna ---
    user_names = ['Semua Pengguna'] + sorted(df_log['name'].unique().tolist())
    selected_name = st.selectbox("Filter berdasarkan Pengguna:", user_names)

    if selected_name != 'Semua Pengguna':
        df_filtered = df_log[df_log['name'] == selected_name]
        
        # Tampilkan Log Spesifik
        st.subheader(f"Log Keluar Masuk Portal Parkir ({selected_name})")
        display_log = df_filtered[['timestamp', 'event_type']].copy()
        display_log['Waktu'] = display_log['timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        display_log.rename(columns={'event_type': 'Tipe Kejadian'}, inplace=True)
        st.dataframe(display_log[['Waktu', 'Tipe Kejadian']], use_container_width=True)
        st.markdown("---")

    else:
        df_filtered = df_log
        st.subheader("Grafik Total Kejadian Parkir")

    # --- Filter Grafik Harian/Mingguan/Bulanan/Tahunan ---
    time_granularity = st.radio(
        "Pilih Granularitas Grafik:", 
        ('Harian', 'Mingguan', 'Bulanan', 'Tahunan'),
        horizontal=True
    )
    
    # Menentukan Agregasi
    if time_granularity == 'Harian':
        df_filtered['DateGroup'] = df_filtered['timestamp'].dt.date
        date_format = "%d %b"
    elif time_granularity == 'Mingguan':
        df_filtered['DateGroup'] = df_filtered['timestamp'].dt.to_period('W').dt.start_time.dt.date
        date_format = "Minggu %W"
    elif time_granularity == 'Bulanan':
        df_filtered['DateGroup'] = df_filtered['timestamp'].dt.to_period('M').dt.start_time.dt.date
        date_format = "%b %Y"
    else: # Tahunan
        df_filtered['DateGroup'] = df_filtered['timestamp'].dt.to_period('Y').dt.start_time.dt.date
        date_format = "%Y"

    # Agregasi Data untuk Grafik
    chart_data = df_filtered.groupby(['DateGroup', 'event_type']).size().reset_index(name='Jumlah')
    
    if chart_data.empty:
        st.warning("Data log tidak mencukupi untuk membuat grafik berdasarkan filter ini.")
        st.stop()

    # Membuat Grafik Altair
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('DateGroup', axis=alt.Axis(title=time_granularity, format=date_format)),
        y=alt.Y('Jumlah', title='Jumlah Transaksi'),
        color='event_type',
        tooltip=['DateGroup', 'event_type', 'Jumlah']
    ).properties(
        title=f"Total Transaksi Parkir ({time_granularity})"
    ).interactive() 

    st.altair_chart(chart, use_container_width=True)
