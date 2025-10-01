def set_background(image_path):
    
    base64_img = get_base64_of_bin_file(image_path)
    
    if base64_img is not None:
        st.markdown(
            f"""
            <style>
            .stApp {{
                /* Menggunakan data:image/jpeg;base64 untuk gambar yang tertanam */
                background-image: url("data:image/jpeg;base64,{base64_img}");
                background-size: cover; 
                background-attachment: fixed; 
                background-position: center;
                /* >>> BARIS KODE BARU UNTUK BLUR (BURAM) FOTO <<< */
                filter: blur(4px); /* Ubah angka 4px sesuai tingkat blur yang diinginkan */
            }}
            /* ... (Sisa CSS Anda untuk sidebar dan konten tetap sama) ... */
            </style>
            """,
            unsafe_allow_html=True
        )
    # ... (sisa fungsi) ...
