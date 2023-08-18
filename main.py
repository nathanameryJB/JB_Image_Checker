import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64

st.set_page_config(layout="wide")
st.title("E-commerce Image Extractor")

st.write('Upload a csv file with a list of product URLs in a column called Product URL')
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])


def extract_images(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    sku = "Unknown SKU"  # Default value for SKU
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')
        base_url = '/'.join(url.split('/')[:3])

        # Extract SKU if possible
        if "/product/" in url:
            sku = url.split("/product/")[1].split("/")[0]

        primary_image = base_url + soup.select("#primary-image > div > div > div > img")[0]['src']
        images = [primary_image]

        for i in range(2, 12):
            selector = f"#slide_1_{i} > div > div > div > img"
            elems = soup.select(selector)
            if elems:
                images.append(base_url + elems[0]['src'])
            else:
                break

        return [sku, url] + images

    except Exception as e:
        return [sku, url, str(e)] + ['Error'] * 10


if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)

    urls = df['Product URL'].tolist()

    # Initialize progress bar and text
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0)
    my_text = st.empty()

    data = []
    max_num_images = 1

    for i, url in enumerate(urls):
        row_data = extract_images(url)
        data.append(row_data)
        max_num_images = max(max_num_images, len(row_data) - 2)  # subtracting 2 for SKU and URL

        # Update the progress bar
        progress_text = f"Processing URL {i + 1}/{len(urls)}: {url}"
        my_text.text(progress_text)
        my_bar.progress((i + 1) / len(urls))
        if (i+1 == len(urls)):
            progress_text = f"All images complete!"
            my_text.text(progress_text)

    columns = ["Sku", "Product URL"] + [f"Image{i + 1}" for i in range(max_num_images)]
    results_df = pd.DataFrame(data, columns=columns)

    st.write(results_df)
    csv = results_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="extracted_data.csv">Download CSV File</a>'
    st.markdown(href, unsafe_allow_html=True)
