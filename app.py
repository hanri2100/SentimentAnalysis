import pandas as pd
import streamlit as st

import preprocessing_logic as pl
import visualization_logic as vl

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_icon="📊",
    page_title="Dashboard Analisis Teks",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS HACK UNTUK MENGURANGI ATAU MENAMBAHKAN PADDING DI TIAP SISI ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 9rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        [data-testid="stSidebar"] hr {
            margin-top: 0 !important;
            margin-bottom: 10px !important;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0rem !important; 
        }
    </style>
""", unsafe_allow_html=True)

# --- Inisialisasi State ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.data_processed = False
    st.session_state.original_df = None
    st.session_state.processed_df = None
    st.session_state.selected_language = "Bahasa Indonesia"
    st.session_state.selected_column = None
    st.session_state.active_dataset_name = ""
    st.session_state.datasets = {}

# Load NLTK resources
pl.load_nltk_resources()

# --- UI Aplikasi ---

st.title("Dashboard Preprocessing & Analisis Teks")

# --- Sidebar: Data Manager ---
with st.sidebar:
    #st.title("🗃️ Data Manager")
    st.markdown(
        """
        <h1 style='text-align: left; font-size: 28px; margin-top: -45px; margin-bottom: 0px;'>
            🗃️ Data Manager
        </h1>
        """, 
        unsafe_allow_html=True
    )
    
    st.write("### Upload File")
    uploaded_files = st.file_uploader(
        "Upload CSV atau xlxs (Bisa banyak file sekaligus)",
        # UBAH DI SINI: Tambahkan "xlsx" ke dalam list type
        type=["csv", "xlsx"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.datasets:
                try:
                    # UBAH DI SINI: Logika pengecekan tipe file
                    if uploaded_file.name.endswith('.xlsx'):
                        # Baca sebagai Excel
                        df_temp = pd.read_excel(uploaded_file)
                    else:
                        # Baca sebagai CSV (Default)
                        df_temp = pd.read_csv(uploaded_file)
                    
                    st.session_state.datasets[uploaded_file.name] = df_temp
                    st.toast(f"Dataset '{uploaded_file.name}' dimuat!", icon="✅")
                except Exception as e:
                    st.error(f"Gagal memuat {uploaded_file.name}: {e}")
    #st.divider()
    #'''st.markdown("""
        #<hr style="margin-top: 0px; margin-bottom: 0px; border: none; height: 1px; background-color: #444;">
    #""", unsafe_allow_html=True)'''

    st.write("### Pilih Dataset Aktif")
    if not st.session_state.datasets:
        st.info("Belum ada dataset di library.")
    else:
        dataset_names = list(st.session_state.datasets.keys())

        # Logic untuk mempertahankan pilihan terakhir
        default_ix = 0
        if st.session_state.active_dataset_name in dataset_names:
            default_ix = dataset_names.index(st.session_state.active_dataset_name)

        selected_dataset_name = st.selectbox(
            "Pilih dataset untuk dianalisis:",
            dataset_names,
            index=default_ix
        )

        # Tombol load dataset
        if st.button("📂 Buka Dataset", type="primary", width='stretch'):
            st.session_state.original_df = st.session_state.datasets[selected_dataset_name]
            st.session_state.active_dataset_name = selected_dataset_name
            st.session_state.data_loaded = True

            # Reset processing state saat ganti dataset
            st.session_state.data_processed = False
            st.session_state.processed_df = None
            st.rerun()

        if st.session_state.data_loaded and st.session_state.active_dataset_name:
            st.success(f"Sedang Aktif: **{st.session_state.active_dataset_name}**", icon="🟢")

# --- Tabs ---
tab1, tab2 = st.tabs(["Preprocessing Teks", "Visualisasi Hasil"])

# --- TAB 1: PREPROCESSING ---
with tab1:
    col_icon, col_header = st.columns([1, 12])
    with col_icon:
        try:
            st.image("icon-sentimenty-analysis.png", width='stretch')
        except:
            st.write("⚙️")
    with col_header:
        st.header("Pipeline Preprocessing")

    if not st.session_state.data_loaded:
        st.info("Silakan upload dan pilih dataset di sidebar.")
    else:
        st.divider()

        # Konfigurasi
        st.subheader("Konfigurasi & Kolom")
        col_conf1, col_conf2, col_empty = st.columns([1, 1, 2])

        with col_conf1:
            st.markdown("**Bahasa Dokumen:**")
            lang_option = st.selectbox(
                "Pilih bahasa (untuk Stopwords/Stemmer):",
                ("Bahasa Indonesia", "English"),
                key="lang_select"
            )
            st.session_state.selected_language = lang_option

        with col_conf2:
            st.markdown("**Kolom Teks Target:**")
            cols = st.session_state.original_df.columns.tolist()

            # Auto-detect kolom
            def_idx = 0
            for i, c in enumerate(cols):
                if "komentar" in c.lower() or "text" in c.lower() or "content" in c.lower():
                    if "jumlah" not in c.lower():
                        def_idx = i
                        break

            st.session_state.selected_column = st.selectbox(
                "Pilih kolom berisi teks:",
                cols,
                index=def_idx
            )

        total_rows = len(st.session_state.original_df)
        with st.expander(f"🔍 Lihat Preview Data Mentah (Total: {total_rows:,} baris)"):
            st.caption("Menampilkan 10 baris pertama saja untuk preview.")
            st.dataframe(st.session_state.original_df.head(10), width='stretch')

        st.divider()

        # Teknik Preprocessing
        st.subheader("Teknik Preprocessing")

        pipeline_steps = {}
        c_tech1, c_tech2 = st.columns(2)

        with c_tech1:
            st.caption("Pembersihan Dasar")
            pipeline_steps['case_folding'] = st.checkbox("Case Folding (Lowercase)", True, disabled=True)
            pipeline_steps['tokenization'] = st.checkbox("Tokenisasi & Simbol Cleaning", True, disabled=True)
            pipeline_steps['stopword_removal'] = st.checkbox("Stopword Removal", True)

        with c_tech2:
            st.caption("Normalisasi Lanjutan")
            pipeline_steps['normalization'] = st.checkbox("Normalisasi Kata Baku (Kamus)", False)

            if st.session_state.selected_language == "Bahasa Indonesia":
                pipeline_steps['stemming'] = st.checkbox("Stemming (Sastrawi)", True)
            else:
                pipeline_steps['lemmatization'] = st.checkbox("Lemmatization (NLTK)", True)

        st.write("")

        # Tombol Eksekusi
        col_btn, col_empty = st.columns([1, 4])  # Rasio 1:4 agar tombol kecil di kiri
        with col_btn:
            start_process = st.button("🚀 Mulai Proses", type="primary", width='stretch')

        if start_process:
            if st.session_state.selected_column:
                with st.spinner("Sedang memproses..."):
                    df_proc = st.session_state.original_df.copy()
                    lang_code = 'id' if st.session_state.selected_language == "Bahasa Indonesia" else 'en'

                    # Apply Pipeline
                    results = df_proc[st.session_state.selected_column].astype(str).apply(
                        lambda x: pl.preprocess_pipeline(x, pipeline_steps, lang_code)
                    )

                    # Explode results to columns
                    df_res = pd.DataFrame(results.tolist(), index=results.index)
                    df_res.columns = ['Teks_Clean', 'Tokens_Awal', 'Tokens_Filtered', 'Tokens_Stemmed', 'Teks_Final_Joined']

                    df_proc = df_proc.join(df_res)
                    df_proc['Jumlah_Tokens_Akhir'] = df_res['Tokens_Stemmed'].apply(len)

                    if 'No' not in df_proc.columns:
                        df_proc.insert(0, 'No', range(1, len(df_proc) + 1))

                    st.session_state.processed_df = df_proc
                    st.session_state.data_processed = True
                    st.rerun()
            else:
                st.error("Pilih kolom teks dulu!")

        # 4. Hasil
        if st.session_state.data_processed:
            st.divider()
            st.subheader("Hasil Preprocessing Lengkap")

            # Pesan Total Data
            total_rows = len(st.session_state.processed_df)
            st.info(f"✅ **Sukses!** Total data berhasil diproses: **{total_rows}** baris.")

            # Display Table
            disp_df = st.session_state.processed_df.copy()
            disp_df.rename(columns={st.session_state.selected_column: 'Teks Asli'}, inplace=True)

            # Convert lists to string for display
            for col in ['Tokens_Awal', 'Tokens_Filtered', 'Tokens_Stemmed']:
                if col in disp_df.columns:
                    disp_df[col] = disp_df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))

            cols_show = ['No', 'Teks Asli', 'Teks_Clean', 'Tokens_Filtered', 'Tokens_Stemmed']
            cols_final = [c for c in cols_show if c in disp_df.columns]

            st.dataframe(disp_df[cols_final], width='stretch', hide_index=True)

            # Download Pertama
            csv = pl.convert_df_to_csv(disp_df[cols_final])
            st.download_button(
                label="📥 Unduh Hasil Ini",
                data=csv,
                file_name=f"clean_full_{st.session_state.active_dataset_name}",
                mime="text/csv"
            )

            # --- INI BAGIAN TABEL RINGKAS ---
            st.divider()
            st.subheader("📄 Hasil Ringkas (User & Komentar Bersih)")

            st.write("Pilih kolom yang berisi **Nama User** untuk ditampilkan berdampingan dengan hasil akhir:")

            # 1. Dropdown untuk memilih kolom User (karena nama kolom bisa beda-beda)
            all_columns = st.session_state.original_df.columns.tolist()

            # Logic menebak kolom user secara otomatis
            user_idx_pred = 0
            for i, col in enumerate(all_columns):
                if "user" in col.lower() or "nama" in col.lower() or "author" in col.lower():
                    user_idx_pred = i
                    break
            col_user_input, col_spacer = st.columns([1, 3]) 
            
            with col_user_input:
                selected_user_col = st.selectbox(
                    "Kolom Nama User:", 
                    all_columns, 
                    index=user_idx_pred,
                    key="select_user_col_final"
                )

            # 2. Membuat Dataframe Khusus (User + Teks Final)
            if selected_user_col and 'Teks_Final_Joined' in st.session_state.processed_df.columns:
                simple_df = pd.DataFrame()
                # Ambil kolom user dari data asli (pastikan index aman)
                simple_df['Nama User'] = st.session_state.processed_df[selected_user_col]
                # Ambil hasil processing
                simple_df['Komentar Hasil Akhir'] = st.session_state.processed_df['Teks_Final_Joined']

                # Tampilkan Tabel
                st.dataframe(simple_df, width='stretch', hide_index=True)

                # 3. Tombol Download Khusus
                csv_simple = pl.convert_df_to_csv(simple_df)
                st.download_button(
                    label="📥 Unduh (User + Komentar)",
                    data=csv_simple,
                    file_name=f"clean_simple_{st.session_state.active_dataset_name}",
                    mime="text/csv"
                )
            # --- AKHIR BAGIAN TABEL RINGKAS ---

# --- TAB 2: VISUALISASI ---
with tab2:
    st.header("📊 Visualisasi Data")

    if not st.session_state.data_loaded:
        st.warning("Pilih dataset di sidebar dulu.")
    elif not st.session_state.selected_column:
        st.warning("Pilih kolom teks di Tab Preprocessing dulu.")
    else:
        # Visualisasi Data Mentah
        st.subheader("Data Mentah (Sebelum)")
        with st.spinner("Generate visualisasi awal..."):
            raw_series = st.session_state.original_df[st.session_state.selected_column]
            df_freq_raw = vl.calculate_word_frequency(raw_series, is_tokenized=False)

            if not df_freq_raw.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Word Cloud**")
                    wc_raw = vl.create_wordcloud(dict(zip(df_freq_raw['Kata'], df_freq_raw['Frekuensi'])))
                    st.image(wc_raw.to_array(), width='stretch')
                with c2:
                    st.write("**Top Kata (Raw)**")
                    fig_raw = vl.plot_word_frequency_seaborn(df_freq_raw)
                    st.pyplot(fig_raw)
            else:
                st.warning("Data mentah kosong/tidak terbaca.")

        st.divider()

        # Visualisasi Data Bersih
        st.subheader("Data Bersih (Sesudah)")

        if not st.session_state.data_processed:
            st.info("💡 Jalankan proses di Tab 1 untuk melihat hasil ini.")
        else:
            # Statistik
            stats_col1, stats_col2 = st.columns(2)
            avg_bef, avg_aft = vl.calculate_basic_stats(
                st.session_state.processed_df[st.session_state.selected_column],
                st.session_state.processed_df['Teks_Final_Joined']
            )

            stats_col1.metric("Avg Kata (Sebelum)", f"{avg_bef:.1f}")
            stats_col2.metric("Avg Kata (Sesudah)", f"{avg_aft:.1f}", delta=f"{avg_aft - avg_bef:.1f}")

            # Plotting
            with st.spinner("Generate visualisasi akhir..."):
                clean_series = st.session_state.processed_df['Tokens_Stemmed']
                df_freq_clean = vl.calculate_word_frequency(clean_series, is_tokenized=True)

                if not df_freq_clean.empty:
                    c3, c4 = st.columns(2)
                    with c3:
                        st.write("**Word Cloud (Clean)**")
                        wc_clean = vl.create_wordcloud(dict(zip(df_freq_clean['Kata'], df_freq_clean['Frekuensi'])))
                        st.image(wc_clean.to_array(), width='stretch')
                    with c4:
                        st.write("**Top Kata (Clean)**")
                        fig_clean = vl.plot_word_frequency_seaborn(df_freq_clean)
                        st.pyplot(fig_clean)
