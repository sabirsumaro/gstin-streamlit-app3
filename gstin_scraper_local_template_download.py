import streamlit as st
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import base64
import os

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def extract_data(gstin):
    try:
        driver = setup_driver()
        driver.get("https://services.gst.gov.in/services/searchtp")
        time.sleep(2)

        search_input = driver.find_element(By.ID, "forGstin")
        search_input.send_keys(gstin)
        driver.find_element(By.ID, "searchGstin").click()
        time.sleep(3)

        legal_name = driver.find_element(By.XPATH, '//*[text()="Legal Name of Business"]/following-sibling::*').text
        trade_name = driver.find_element(By.XPATH, '//*[text()="Trade Name"]/following-sibling::*').text
        principal_place = driver.find_element(By.XPATH, '//*[text()="Principal Place of Business"]/following-sibling::*').text
        additional_place = driver.find_element(By.XPATH, '//*[text()="Additional Place of Business"]/following-sibling::*').text
        jurisdiction = driver.find_element(By.XPATH, '//*[text()="State Jurisdiction"]/following-sibling::*').text

        driver.quit()
        return {
            "GSTIN": gstin,
            "Trade Name": trade_name,
            "Legal Name": legal_name,
            "Principal Place": principal_place,
            "Additional Place": additional_place,
            "State Jurisdiction": jurisdiction,
            "Error": ""
        }
    except Exception as e:
        return {"GSTIN": gstin, "Trade Name": "", "Legal Name": "", "Principal Place": "", "Additional Place": "", "State Jurisdiction": "", "Error": str(e)}

st.set_page_config(page_title="GSTIN Scraper – IRIS GST", layout="centered")

st.title("📄 GSTIN Scraper (IRIS GST) – Local App")

st.markdown("### 🧩 Step 1: Download Sample Excel Template")
st.markdown('[📥 Click here to download GSTIN_Template.xlsx](https://github.com/sabirsumaro/gstin-render-app1/raw/main/GSTIN_Template.xlsx)', unsafe_allow_html=True)

st.markdown("### 📤 Step 2: Upload the filled Excel File")

uploaded_file = st.file_uploader("Upload Excel file with GSTINs", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    gstin_list = df.iloc[:, 0].dropna().astype(str).tolist()
    results = []

    progress_text = "⏳ Extracting GSTIN details..."
    my_bar = st.progress(0, text=progress_text)

    def fetch_and_append(gstin):
        result = extract_data(gstin)
        results.append(result)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i, _ in enumerate(executor.map(fetch_and_append, gstin_list)):
            my_bar.progress((i + 1) / len(gstin_list), text=progress_text)

    my_bar.empty()
    st.success("✅ Extraction Complete!")

    output_df = pd.DataFrame(results)
    output_file = "GSTIN_Results.xlsx"
    output_df.to_excel(output_file, index=False)

    with open(output_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="GSTIN_Results.xlsx">📥 Download Extracted Excel</a>'
        st.markdown(href, unsafe_allow_html=True)
