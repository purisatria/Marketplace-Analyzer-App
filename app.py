import streamlit as st
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from collections import Counter

# -----------------------------
# Shopee Scraper
# -----------------------------
def scrape_shopee(keyword, limit=50):
    results = []
    for offset in range(0, limit, 50):
        url = f"https://shopee.co.id/api/v4/search/search_items?by=relevancy&keyword={keyword}&limit=50&newest={offset}&order=desc&page_type=search"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://shopee.co.id/search?keyword={keyword}"
        }
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
        except Exception as e:
            st.error(f"❌ Gagal mengambil data dari Shopee: {e}")
            return []
        data = res.json()
        items = data.get("items", [])
        for item in items:
            p = item.get("item_basic", {})
            results.append({
                "platform": "Shopee",
                "nama_produk": p.get('name', ''),
                "harga": p.get('price', 0) / 100000,
                "terjual": p.get('historical_sold', 0),
                "rating": p.get('item_rating', {}).get('rating_star', 0),
                "lokasi": p.get('shop_location', 'Tidak diketahui')
            })
        time.sleep(1)
    return results

# -----------------------------
# Tokopedia Scraper
# -----------------------------
def scrape_tokopedia(keyword, limit=2):
    results = []
    for page in range(1, limit + 1):
        url = f"https://www.tokopedia.com/search?st=product&q={keyword}&page={page}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
        except Exception as e:
            st.error(f"❌ Gagal mengambil data dari Tokopedia: {e}")
            return []
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if '__INITIAL_STATE__=' in script.text:
                raw = script.text.split('__INITIAL_STATE__=')[-1].rstrip(';')
                try:
                    import json
                    data = json.loads(raw)
                    products = data.get('search', {}).get('data', {}).get('products', [])
                    for p in products:
                        results.append({
                            "platform": "Tokopedia",
                            "nama_produk": p.get('name', ''),
                            "harga": p.get('price', 0),
                            "terjual": p.get('countSold', 0),
                            "rating": p.get('rating', 0),
                            "lokasi": p.get('shop', {}).get('location', 'Tidak diketahui')
                        })
                except Exception:
                    continue
        time.sleep(1)
    return results

# -----------------------------
# SEO Keyword Analyzer
# -----------------------------
def analisis_keyword(nama_produk_list):
    semua_kata = []
    for nama in nama_produk_list:
        kata = nama.lower().split()
        semua_kata.extend(kata)
    return Counter(semua_kata).most_common(10)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Marketplace Analyzer", layout="wide")
st.title("🛍️ Marketplace Keyword Analyzer")

keyword = st.text_input("Masukkan Keyword Pencarian:", "sepatu olahraga")
platforms = st.multiselect("Pilih Marketplace:", ["Shopee", "Tokopedia"], default=["Shopee", "Tokopedia"])

if st.button("🔍 Mulai Analisis"):
    all_results = []

    if "Shopee" in platforms:
        with st.spinner("Mengambil data dari Shopee..."):
            scr = scrape_shopee(keyword)
            if not scr:
                st.error("Shopee mengembalikan data kosong.")
            all_results += scr

    if "Tokopedia" in platforms:
        with st.spinner("Mengambil data dari Tokopedia..."):
            scr = scrape_tokopedia(keyword)
            if not scr:
                st.error("Tokopedia mengembalikan data kosong.")
            all_results += scr

    if not all_results:
        st.warning("Tidak ada data ditemukan. Coba keyword lain atau cek koneksi.")
    else:
        df = pd.DataFrame(all_results)
        st.subheader("📊 Hasil Scraping Produk")
        st.dataframe(df)

        st.subheader("📈 Statistik dan Analisis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Jumlah Produk", len(df))
            st.metric("Rata-rata Harga", f"Rp {round(df['harga'].mean(), 2):,}")
        with col2:
            st.metric("Rata-rata Rating", round(df['rating'].mean(), 2))
            st.metric("Total Terjual", int(df['terjual'].sum()))

        st.subheader("🔠 Keyword Umum di Judul Produk")
        keyword_df = pd.DataFrame(analisis_keyword(df['nama_produk']), columns=["Keyword", "Frekuensi"])
        st.table(keyword_df)

        st.subheader("⬇️ Ekspor Data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="hasil_scraping.csv", mime="text/csv")
