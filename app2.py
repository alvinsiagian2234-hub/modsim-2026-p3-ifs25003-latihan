import streamlit as st
import simpy
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import plotly.express as px
import plotly.graph_objects as go

# =====================================
# STRUKTUR PARAMETER SIMULASI
# =====================================
@dataclass
class ParameterSimulasi:
    TOTAL_MEJA: int
    ORANG_PER_MEJA: int
    PETUGAS_LAUK: int
    PETUGAS_ANGKUT: int
    PETUGAS_NASI: int
    JAM_MULAI: int
    MENIT_MULAI: int
    SEED_RANDOM: int = 42


# =====================================
# MODEL DISCRETE EVENT SIMULATION
# =====================================
class ModelPiket:

    def __init__(self, param: ParameterSimulasi):
        self.environment = simpy.Environment()
        self.param = param
        random.seed(param.SEED_RANDOM)

        # Total ompreng yang diproses
        self.jumlah_ompreng = param.TOTAL_MEJA * param.ORANG_PER_MEJA

        # Resource tiap tahapan
        self.resource_lauk = simpy.Resource(self.environment, capacity=param.PETUGAS_LAUK)
        self.resource_angkut = simpy.Resource(self.environment, capacity=param.PETUGAS_ANGKUT)
        self.resource_nasi = simpy.Resource(self.environment, capacity=param.PETUGAS_NASI)

        self.hasil = []
        self.waktu_awal = datetime(2024, 1, 1, param.JAM_MULAI, param.MENIT_MULAI)

    def konversi_waktu(self, menit_simulasi):
        return self.waktu_awal + timedelta(minutes=menit_simulasi)

    def alur_ompreng(self, id_data):

        mulai = self.environment.now

        # Tahap 1: Isi lauk
        with self.resource_lauk.request() as req:
            yield req
            durasi_lauk = random.uniform(0.5, 1)
            yield self.environment.timeout(durasi_lauk)

        # Tahap 2: Pengangkutan
        with self.resource_angkut.request() as req:
            yield req
            durasi_angkut = random.uniform(0.33, 1)
            yield self.environment.timeout(durasi_angkut)

        # Tahap 3: Isi nasi
        with self.resource_nasi.request() as req:
            yield req
            durasi_nasi = random.uniform(0.5, 1)
            yield self.environment.timeout(durasi_nasi)

        selesai = self.environment.now

        self.hasil.append({
            "ID Ompreng": id_data,
            "Waktu Mulai (menit)": mulai,
            "Waktu Selesai (menit)": selesai,
            "Total Durasi (menit)": selesai - mulai,
            "Jam Selesai": self.konversi_waktu(selesai)
        })

    def jalankan(self):
        for i in range(self.jumlah_ompreng):
            self.environment.process(self.alur_ompreng(i))
        self.environment.run()
        return pd.DataFrame(self.hasil)


# =====================================
# APLIKASI STREAMLIT
# =====================================
def main():

    st.set_page_config(
        page_title="Simulasi Sistem Piket IT Del",
        page_icon="🍱",
        layout="wide"
    )

    # ===== SIDEBAR =====
    with st.sidebar:
        st.header("⚙️ Pengaturan Simulasi")

        total_meja = st.number_input("Jumlah Meja", 10, 200, 60)
        orang_meja = st.number_input("Mahasiswa per Meja", 1, 5, 3)

        st.divider()
        st.subheader("👨‍🍳 Petugas")

        petugas_lauk = st.number_input("Pengisi Lauk", 1, 5, 2)
        petugas_angkut = st.number_input("Pengangkut Ompreng", 1, 5, 2)
        petugas_nasi = st.number_input("Pengisi Nasi", 1, 5, 3)

        st.divider()
        st.subheader("🕐 Waktu Mulai")

        jam_mulai = st.slider("Jam", 0, 23, 7)
        menit_mulai = st.slider("Menit", 0, 59, 0)

        tombol_run = st.button("🚀 Jalankan Simulasi", use_container_width=True)

    # ===== HEADER =====
    st.title("🍱 Simulasi Sistem Piket IT Del")
    st.markdown("""
    **Model Discrete Event Simulation (DES)**  
    Tahapan proses:
    1. Pengisian Lauk  
    2. Pengangkutan Ompreng  
    3. Pengisian Nasi  
    """)

    if not tombol_run:
        st.info("""
        ### Cara Menggunakan:
        1. Atur parameter di sidebar  
        2. Klik tombol Jalankan Simulasi  
        3. Analisis hasil yang muncul  
        """)
        return

    # ===== EKSEKUSI SIMULASI =====
    parameter = ParameterSimulasi(
        total_meja,
        orang_meja,
        petugas_lauk,
        petugas_angkut,
        petugas_nasi,
        jam_mulai,
        menit_mulai
    )

    simulasi = ModelPiket(parameter)
    dataframe = simulasi.jalankan()

    total_waktu = dataframe["Waktu Selesai (menit)"].max()
    rata_durasi = dataframe["Total Durasi (menit)"].mean()

    # ===== METRIC =====
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Ompreng", total_meja * orang_meja)
    m2.metric("Waktu Selesai (menit)", f"{total_waktu:.2f}")
    m3.metric("Rata-rata Durasi", f"{rata_durasi:.2f}")
    m4.metric("Selesai Jam", simulasi.konversi_waktu(total_waktu).strftime("%H:%M"))

    st.divider()

    # ===== VISUALISASI =====
    c1, c2 = st.columns(2)

    with c1:
        histogram = px.histogram(
            dataframe,
            x="Total Durasi (menit)",
            nbins=30,
            title="Distribusi Total Waktu Penyelesaian"
        )
        st.plotly_chart(histogram, use_container_width=True)

    with c2:
        scatter = px.scatter(
            dataframe,
            x="Waktu Selesai (menit)",
            y="ID Ompreng",
            title="Timeline Penyelesaian Ompreng"
        )
        st.plotly_chart(scatter, use_container_width=True)

    st.divider()

    # ===== GRAFIK PETUGAS =====
    grafik_petugas = go.Figure()

    grafik_petugas.add_trace(go.Bar(name="Pengisi Lauk", x=["Lauk"], y=[petugas_lauk]))
    grafik_petugas.add_trace(go.Bar(name="Pengangkut Ompreng", x=["Angkut"], y=[petugas_angkut]))
    grafik_petugas.add_trace(go.Bar(name="Pengisi Nasi", x=["Nasi"], y=[petugas_nasi]))

    grafik_petugas.update_layout(
        barmode='group',
        title="Jumlah Petugas per Tahap"
    )

    st.plotly_chart(grafik_petugas, use_container_width=True)

    st.divider()

    # ===== DATAFRAME =====
    st.subheader("📄 Detail Data Simulasi")
    st.dataframe(dataframe, use_container_width=True)

    csv_file = dataframe.to_csv(index=False).encode()
    st.download_button(
        "📥 Download CSV",
        csv_file,
        "hasil_simulasi_piket_ITDel.csv",
        "text/csv",
        use_container_width=True
    )

    st.caption("MODSIM - Discrete Event Simulation | IT Del")


if __name__ == "__main__":
    main()