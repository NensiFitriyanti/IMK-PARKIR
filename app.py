# app.py
import streamlit as st
import pandas as pd
import uuid
import qrcode
from io import BytesIO
import os

# --- Konfigurasi ---
DATA_FILE = 'parking_users.csv'

# --- Fungsi Pembantu (Utilities) ---

def load_data():
    """Memuat data dari CSV atau membuat DataFrame baru jika file tidak ada."""
    if os.path.exists(DATA_FILE):
        # Baca data yang sudah ada
        df = pd.read_csv(DATA_FILE)
    else:
        # Buat DataFrame kosong jika file belum ada
        df = pd.DataFrame(columns=['barcode_id', 'name', 'user_id', 'vehicle_type', 'license_plate', 'status'])
    
    # Atur barcode_id sebagai index
    df = df.set_index('barcode_id', drop=False)
    return df

def save_data(df):
    """Menyimpan DataFrame ke file CSV."""
    df.to_csv(DATA_FILE, index=False)

def generate_qr_code(data):
    """Menghasilkan gambar QR code (Barcode) di memori."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # Data yang dimasukkan ke QR code adalah ID unik pengguna
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Simpan gambar ke buffer memori
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# --- Aplikasi Utama Streamlit ---

st.set_page_config(layout="wide", page_title="Dashboard Parkir Barcode")

st.title("🅿️ Aplikasi Dashboard Parkir Barcode")

# 1. Inisialisasi Session State
# Memastikan data (DataFrame) dimuat hanya sekali saat aplikasi dimulai
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Tata letak 2 kolom
col1, col2 = st.columns([1, 2]) # Kolom 1 lebih kecil untuk formulir, Kolom 2 lebih besar untuk dashboard

# =================================================================
# KOLOM 1: PENDAFTARAN & GENERASI BARCODE
# =================================================================
with col1:
    st.header("1. Pendaftaran Pengguna Parkir")
    
    # Formulir Pendaftaran
    with st.form("registration_form"):
        name = st.text_input("Nama Lengkap")
        user_id = st.text_input("NIM/NIP")
        vehicle_type = st.selectbox("Jenis Kendaraan", ['Motor', 'Mobil'])
        license_plate = st.text_input("Nomor Polisi (Nopol)").upper()
        
        submitted = st.form_submit_button("Daftar & Buat Barcode")

        if submitted:
            if name and user_id and license_plate:
                # 1. Buat ID unik (Data yang akan tersimpan di Barcode)
                new_barcode_id = str(uuid.uuid4())
                
                # 2. Buat baris data baru
                new_data = {
                    'barcode_id': new_barcode_id,
                    'name': name,
                    'user_id': user_id,
                    'vehicle_type': vehicle_type,
                    'license_plate': license_plate,
                    'status': 'OUT' # Status awal: Di luar (OUT)
                }
                
                # 3. Tambahkan ke DataFrame dan simpan ke CSV
                st.session_state.data.loc[new_barcode_id] = new_data
                save_data(st.session_state.data)
                
                st.success("Pendaftaran berhasil! Barcode Anda telah dibuat.")
                
                # 4. Tampilkan Barcode
                st.subheader("Barcode Akses Anda (QR Code)")
                qr_buffer = generate_qr_code(new_barcode_id)
                st.image(qr_buffer, caption=f"ID: {new_barcode_id[:8]}...", width=250)
                st.download_button(
                    label="Download Barcode (PNG)",
                    data=qr_buffer,
                    file_name=f"{name}_parkir.png",
                    mime="image/png"
                )
            else:
                st.error("Semua kolom harus diisi!")

# =================================================================
# KOLOM 2: DASHBOARD & SIMULASI SCAN
# =================================================================
with col2:
    st.header("2. Dashboard Parkir & Simulasi Scan")
    
    # --- Simulasi Gerbang (Scanner) ---
    st.subheader("Simulasi Scan Barcode Gerbang")
    # Di dunia nyata, ini adalah ID yang dibaca oleh pemindai di gerbang.
    scan_id = st.text_input("Masukkan Barcode ID (Salin dari Kolom Kiri):", 
                            help="Ini mensimulasikan data yang dikirim oleh pemindai barcode.")
    scan_button = st.button("Simulasi SCAN")
    
    if scan_button and scan_id:
        scan_id = scan_id.strip()
        # Cek apakah ID Barcode ada di data
        if scan_id in st.session_state.data.index:
            user_row = st.session_state.data.loc[scan_id]
            current_status = user_row['status']
            name = user_row['name']
            
            # Logika Pintu Masuk/Keluar
            if current_status == 'OUT':
                new_status = 'IN'
                action = "MASUK"
                st.success(f"✅ GERBANG TERBUKA! Selamat {action}, {name}. Status baru: DI DALAM.")
            else: # Status is 'IN'
                new_status = 'OUT'
                action = "KELUAR"
                st.info(f"🚪 GERBANG TERBUKA! Selamat {action}, {name}. Status baru: DI LUAR.")
            
            # Perbarui status di DataFrame dan simpan ke CSV
            st.session_state.data.loc[scan_id, 'status'] = new_status
            save_data(st.session_state.data)
            
            # Refresh komponen dashboard
            st.experimental_rerun() 
            
        else:
            st.error("❌ Barcode ID tidak terdaftar!")

    st.markdown("---")
    
    # --- Tabel Status Parkir ---
    st.subheader("Status Parkir Saat Ini")
    
    # Tampilkan kolom yang relevan saja
    display_data = st.session_state.data[['name', 'license_plate', 'vehicle_type', 'status']].copy()
    
    # Fungsi untuk mewarnai status (opsional, untuk tampilan lebih baik)
    def color_status(val):
        color = 'lightgreen' if val == 'IN' else 'salmon'
        return f'background-color: {color}'

    # Tampilkan DataFrame dengan pewarnaan
    st.dataframe(
        display_data.style.applymap(color_status, subset=['status']),
        use_container_width=True
    )

    # Tampilkan Metrik Ringkasan
    total_users = len(st.session_state.data)
    parked_count = len(st.session_state.data[st.session_state.data['status'] == 'IN'])
    
    st.metric(label="Total Pengguna Terdaftar", value=total_users)
    st.metric(label="Sedang Parkir (IN)", value=parked_count)