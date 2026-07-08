import streamlit as st
import psycopg2
import pandas as pd

# Sayfa ayarı
st.set_page_config(page_title="İnciroğlu Otomotiv | Müşteri Takip Sistemi", layout="wide")

# Neon.tech Veritabanı Bağlantısı
DB_URL = "postgresql://neondb_owner:npg_0afpRg5dUwAZ@ep-young-violet-at90a7rq.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Veritabanı bağlantı fonksiyonu
def get_connection():
    return psycopg2.connect(DB_URL)

# Veritabanı ve ID (Numaralandırma) Güncellemesi
try:
    conn = get_connection()
    c = conn.cursor()
    # Tablo yoksa oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler 
                 (isim TEXT, model TEXT, danisman TEXT, durum TEXT, notlar TEXT)''')
    
    # Geçmiş kayıtlara ve yeni ekleneceklere "id" sütunu ekleme kontrolü
    c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='musteriler' AND column_name='id'")
    if not c.fetchone():
        c.execute("ALTER TABLE musteriler ADD COLUMN id SERIAL PRIMARY KEY")
        
    conn.commit()
    conn.close()
except Exception as e:
    st.error(f"Veritabanı bağlantı hatası: {e}")

# Sol üst sabit başlık ve Ana Başlık
st.markdown("<h4 style='margin-bottom: -15px; color: #555555;'>İnciroğlu Otomotiv</h4>", unsafe_allow_html=True)
st.title("BMW & MINI Müşteri Takip Sistemi")
st.markdown("---")

# 1. BÖLÜM: Müşteri Giriş Formu
with st.form("musteri_formu", clear_on_submit=True):
    st.subheader("📝 Yeni Müşteri Notu Ekle")
    col1, col2 = st.columns(2)
    isim = col1.text_input("Müşteri İsim Soyisim")
    
    tum_modeller = [
        "BMW 1 Serisi", "BMW 2 Serisi", "BMW 3 Serisi", "BMW 4 Serisi", 
        "BMW 5 Serisi", "BMW 7 Serisi", "BMW i4", "BMW i5", 
        "BMW iX3 50 xDrive", "BMW iX", "BMW i7", "BMW X1", "BMW X2", "BMW X3", "BMW X5", "BMW X7",
        "MINI Countryman", "MINI JCW", "MINI COUNTRYMAN JCW ALL4", "MINI 5 KAPI", "MINI 3 KAPI", "MINI CABRIO",
        "MINI COUNTRYMAN E", "MINI COUNTRYMAN DARK EDITION", "MINI COUNTRYMAN C FAVOURED"
    ]
    model = col2.selectbox("İlgilendiği Model", tum_modeller)
    
    col3, col4 = st.columns(2)
    danismanlar = ["Çavuş Karakaya", "Furkan Benli", "Raife Karakız", "M.Tugay Karsantı", "Arif Yüksel"]
    danisman = col3.selectbox("İlgilenen Danışman", danismanlar)
    durum = col4.selectbox("Satış Durumu", ["Beklemede", "Satış Gerçekleşti", "Kaybedildi"])
    
    notlar = st.text_area("Notlar (Son Görüşme Özeti)")
    
    if st.form_submit_button("➕ Sistemi Kaydet"):
        if isim != "":
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO musteriler (isim, model, danisman, durum, notlar) VALUES (%s, %s, %s, %s, %s)", 
                      (isim, model, danisman, durum, notlar))
            conn.commit()
            conn.close()
            st.success(f"{isim} başarıyla veritabanına kaydedildi!")
            st.rerun()
        else:
            st.warning("Lütfen müşteri ismini giriniz.")

# 2. BÖLÜM: Arama, Listeleme, Güncelleme ve Silme Alanı
st.markdown("---")
st.header("📊 Kayıtlı Müşteriler")

try:
    conn = get_connection()
    # ID dahil tüm verileri çek ve ID'ye göre tersten sırala (En yeni en üstte)
    df = pd.read_sql("SELECT id, isim, model, danisman, durum, notlar FROM musteriler ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        # Tablo başlıklarını daha şık hale getiriyoruz
        df = df.rename(columns={
            "id": "Müşteri ID",
            "isim": "Müşteri Adı",
            "model": "Model",
            "danisman": "Danışman",
            "durum": "Durum",
            "notlar": "Notlar"
        })

        arama_terimi = st.text_input("🔍 Tüm Kayıtlarda Ara (Müşteri Adı, Model, Danışman veya ID No yazın...)", "")
        
        # ARAMA YAPILDIYSA
        if arama_terimi:
            df_filtered = df[
                df['Müşteri Adı'].str.contains(arama_terimi, case=False, na=False) |
                df['Model'].str.contains(arama_terimi, case=False, na=False) |
                df['Danışman'].str.contains(arama_terimi, case=False, na=False) |
                df['Notlar'].str.contains(arama_terimi, case=False, na=False) |
                df['Müşteri ID'].astype(str).str.contains(arama_terimi, case=False, na=False)
            ]
            st.caption("🔎 Arama Sonuçları (Tüm sekmelerdeki veriler tek ekranda listelenir)")
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            
        # ARAMA YAPILMADIYSA NORMAL SEKME GÖRÜNÜMÜ
        else:
            tab1, tab2, tab3 = st.tabs(["✅ Satış Gerçekleşti", "⏳ Beklemede", "❌ Kaybedildi"])
            
            with tab1:
                st.dataframe(df[df["Durum"] == "Satış Gerçekleşti"], use_container_width=True, hide_index=True)
            with tab2:
                st.dataframe(df[df["Durum"] == "Beklemede"], use_container_width=True, hide_index=True)
            with tab3:
                st.dataframe(df[df["Durum"] == "Kaybedildi"], use_container_width=True, hide_index=True)
        
        # GÜNCELLEME VE SİLME PANELLERİ
        st.markdown("<br>", unsafe_allow_html=True)
        col_guncelle, col_sil = st.columns(2)
        
        # SOL PANEL: Durum Güncelleme
        with col_guncelle:
            with st.expander("🔄 Müşteri Durumunu Güncelle"):
                st.info("Kayıtlı bir müşterinin satış durumunu değiştirebilirsiniz.")
                guncelle_id = st.text_input("Durumu Güncellenecek 'Müşteri ID':", key="upd_id")
                yeni_durum = st.selectbox("Yeni Durum Seçin", ["Satış Gerçekleşti", "Beklemede", "Kaybedildi"])
                
                if st.button("🔄 Durumu Kaydet"):
                    if guncelle_id.isdigit():
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE musteriler SET durum = %s WHERE id = %s", (yeni_durum, guncelle_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Müşteri ID: {guncelle_id} başarıyla '{yeni_durum}' olarak güncellendi!")
                        st.rerun()
                    else:
                        st.error("Lütfen geçerli bir sayı (ID) giriniz.")
        
        # SAĞ PANEL: Kayıt Silme
        with col_sil:
            with st.expander("🗑️ Müşteri Kaydı Sil"):
                st.warning("Silinen kayıtlar geri getirilemez!")
                sil_id = st.text_input("Silmek istediğiniz kaydın 'Müşteri ID' numarasını girin:", key="del_id")
                
                if st.button("🗑️ Kalıcı Olarak Sil"):
                    if sil_id.isdigit():
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM musteriler WHERE id = %s", (sil_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Müşteri ID: {sil_id} sistemden tamamen silindi!")
                        st.rerun()
                    else:
                        st.error("Lütfen geçerli bir sayı (ID) giriniz.")

    else:
        st.info("Sistemde henüz kayıtlı müşteri bulunmuyor.")
except Exception as e:
    st.error("Veriler yüklenirken bir hata oluştu.")