import streamlit as st
import simpy
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import plotly.express as px
import plotly.graph_objects as go

# =========================
# KONFIGURASI
# =========================
@dataclass
class Config:
    JUMLAH_MEJA: int
    MAHASISWA_PER_MEJA: int
    PENGISI_LAUK: int
    PENGANGKUT_OMPRENG: int
    PENGISI_NASI: int
    START_HOUR: int
    START_MINUTE: int
    RANDOM_SEED: int = 42


# =========================
# MODEL DES SISTEM PIKET
# =========================
class SistemPiketDES:

    def __init__(self, config: Config):
        self.env = simpy.Environment()
        self.config = config
        random.seed(config.RANDOM_SEED)

        self.total_ompreng = config.JUMLAH_MEJA * config.MAHASISWA_PER_MEJA

        # Resource tiap tahap
        self.lauk = simpy.Resource(self.env, capacity=config.PENGISI_LAUK)
        self.pengangkut = simpy.Resource(self.env, capacity=config.PENGANGKUT_OMPRENG)
        self.nasi = simpy.Resource(self.env, capacity=config.PENGISI_NASI)

        self.data = []
        self.start_time = datetime(2024, 1, 1, config.START_HOUR, config.START_MINUTE)

    def to_clock(self, minute):
        return self.start_time + timedelta(minutes=minute)

    def proses_ompreng(self, id_ompreng):

        waktu_mulai = self.env.now

        # =====================
        # 1. ISI LAUK (30–60 detik)
        # =====================
        with self.lauk.request() as req:
            yield req
            waktu_lauk = random.uniform(0.5, 1)
            yield self.env.timeout(waktu_lauk)

        # =====================
        # 2. PENGANGKUT OMPRENG (20–60 detik)
        # =====================
        with self.pengangkut.request() as req:
            yield req
            waktu_angkut = random.uniform(0.33, 1)
            yield self.env.timeout(waktu_angkut)

        # =====================
        # 3. ISI NASI (30–60 detik)
        # =====================
        with self.nasi.request() as req:
            yield req
            waktu_nasi = random.uniform(0.5, 1)
            yield self.env.timeout(waktu_nasi)

        waktu_selesai = self.env.now

        self.data.append({
            "ID Ompreng": id_ompreng,
            "Waktu Mulai (menit)": waktu_mulai,
            "Waktu Selesai (menit)": waktu_selesai,
            "Total Durasi (menit)": waktu_selesai - waktu_mulai,
            "Jam Selesai": self.to_clock(waktu_selesai)
        })

    def run(self):
        for i in range(self.total_ompreng):
            self.env.process(self.proses_ompreng(i))
        self.env.run()
        return pd.DataFrame(self.data)


# =========================
# STREAMLIT APP
# =========================
def main():

    st.set_page_config(
        page_title="Simulasi Sistem Piket IT Del",
        page_icon="🍱",
        layout="wide"
    )

    # ================= SIDEBAR =================
    with st.sidebar:
        st.header("⚙️ Parameter Simulasi")

        meja = st.number_input("Jumlah Meja", 10, 200, 60)
        mahasiswa = st.number_input("Mahasiswa per Meja", 1, 5, 3)

        st.divider()
        st.subheader("👨‍🍳 Jumlah Petugas")

        lauk = st.number_input("Pengisi Lauk", 1, 5, 2)
        pengangkut = st.number_input("Pengangkut Ompreng", 1, 5, 2)
        nasi = st.number_input("Pengisi Nasi", 1, 5, 3)

        st.divider()
        st.subheader("🕐 Waktu Mulai")

        jam = st.slider("Jam", 0, 23, 7)
        menit = st.slider("Menit", 0, 59, 0)

        run = st.button("🚀 Jalankan Simulasi", use_container_width=True)

    # ================= HEADER =================
    st.title("🍱 Simulasi Sistem Piket IT Del")
    st.markdown("""
    **Model Discrete Event Simulation (DES)**  
    Alur sistem:
    1. Pengisi Lauk  
    2. Pengangkut Ompreng  
    3. Pengisi Nasi  
    """)

    if not run:
        st.info("""
        ### 🚀 Cara Menjalankan:
        1. Atur parameter di sidebar kiri  
        2. Klik tombol **Jalankan Simulasi**  
        3. Lihat hasil dan visualisasi  
        """)
        return

    # ================= JALANKAN SIMULASI =================
    config = Config(
        meja,
        mahasiswa,
        lauk,
        pengangkut,
        nasi,
        jam,
        menit
    )

    model = SistemPiketDES(config)
    df = model.run()

    total_time = df["Waktu Selesai (menit)"].max()
    avg_time = df["Total Durasi (menit)"].mean()

    # ================= METRICS =================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Ompreng", meja * mahasiswa)
    col2.metric("Waktu Selesai (menit)", f"{total_time:.2f}")
    col3.metric("Rata-rata Durasi", f"{avg_time:.2f}")
    col4.metric("Selesai Jam", model.to_clock(total_time).strftime("%H:%M"))

    st.divider()

    # ================= VISUALISASI =================
    colA, colB = st.columns(2)

    with colA:
        fig1 = px.histogram(
            df,
            x="Total Durasi (menit)",
            nbins=30,
            title="Distribusi Total Waktu Penyelesaian"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        fig2 = px.scatter(
            df,
            x="Waktu Selesai (menit)",
            y="ID Ompreng",
            title="Timeline Penyelesaian Ompreng"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ================= GRAFIK PETUGAS =================
    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(name="Pengisi Lauk", x=["Lauk"], y=[lauk]))
    fig_bar.add_trace(go.Bar(name="Pengangkut Ompreng", x=["Angkut"], y=[pengangkut]))
    fig_bar.add_trace(go.Bar(name="Pengisi Nasi", x=["Nasi"], y=[nasi]))

    fig_bar.update_layout(
        barmode='group',
        title="Jumlah Petugas per Tahap"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ================= DATA =================
    st.subheader("📄 Detail Data Simulasi")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button(
        "📥 Download CSV",
        csv,
        "hasil_simulasi_piket_ITDel.csv",
        "text/csv",
        use_container_width=True
    )

    st.caption("MODSIM - Discrete Event Simulation | IT Del")


if __name__ == "__main__":
    main()