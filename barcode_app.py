
import pandas as pd
import streamlit as st
from io import BytesIO
import zipfile

st.set_page_config(page_title="Clinical Barcode Generator", page_icon="🧬")
st.title("🧬 Clinical Trial Barcode Generator")
st.markdown("Upload your raw Excel file to automatically generate barcode Excel files for each treatment arm.")

# ------------------------
# 1️⃣ Upload file
# ------------------------
uploaded_file = st.file_uploader("Upload raw Excel file (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # ------------------------
    # 2️⃣ Read raw Excel
    # ------------------------
    df = pd.read_excel(uploaded_file)

    # ------------------------
    # 3️⃣ Clean & standardize columns
    # ------------------------
    df = df[['Patient ID', 'Treatment arm', 'PK']]  # Keep only relevant columns
    df['Patient ID'] = df['Patient ID'].str.replace('CM-', '', regex=False)  # Remove CM- prefix
    df['Treatment arm'] = 'G' + df['Treatment arm'].astype(str)  # Add G prefix
    df = df.rename(columns={
        'Patient ID': 'ID',
        'Treatment arm': 'Treatment arm',
        'PK': 'PK'
    })

    st.success("✅ Data cleaned successfully!")
    st.dataframe(df.head())  # Optional: preview cleaned data

    # ------------------------
    # 4️⃣ Barcode logic
    # ------------------------
    pk_timepoints_11 = ['P1','P2','P3','P4','P5','P6','P8','P12','P18','P24','P27']
    pk_timepoints_8 = ['P1','P2','P3','P4','P6','P12','P18','P24']

    arm_info = {
        'G1': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_11, 'pk_last_day':14, 'pk_first_day':1},
        'G2': {'mid':None, 'last':'EOT',  'pk_times':pk_timepoints_11, 'pk_last_day':7,  'pk_first_day':1},
        'G3': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_11, 'pk_last_day':14, 'pk_first_day':1},
        'G4': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_8,  'pk_last_day':14, 'pk_first_day':1},
        'G5': {'mid':14,'last':'EOT','pk_times':pk_timepoints_8,  'pk_last_day':28, 'pk_first_day':1},
        'G6': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_8,  'pk_last_day':14, 'pk_first_day':1},
    }

    def generate_barcodes(row):
        barcodes = []
        arm = row['Treatment arm']
        pid = row['ID']
        pk = row['PK'] == 'Yes'
        
        if arm not in arm_info:
            return barcodes
        
        info = arm_info[arm]

        # Mid-treatment
        if info['mid']:
            for sample in ['Pl','Se']:
                for label_type in ['H', 'L']:
                    barcodes.append(f"{arm}D{info['mid']}.{sample}.{pid}")
        
        # End-of-treatment
        for sample in ['Pl','Se','Ur']:
            for label_type in ['H','L']:
                barcodes.append(f"{arm}D{info['last']}.{sample}.{pid}")
        
        # PK collections
        if pk:
            for day in [info['pk_first_day'], info['pk_last_day']]:
                for tp in info['pk_times']:
                    for aliquot in range(1,5):
                        barcodes.append(f"{arm}D{day}.{tp}.{aliquot}.{pid}")
        
        return barcodes

    # ------------------------
    # 5️⃣ Generate all barcodes
    # ------------------------
    all_barcodes = []
    for _, row in df.iterrows():
        bcs = generate_barcodes(row)
        all_barcodes.extend([(row['Treatment arm'], row['ID'], bc) for bc in bcs])

    barcode_df = pd.DataFrame(all_barcodes, columns=['Arm','ID','Barcode'])

    # ------------------------
    # 6️⃣ Download options
    # ------------------------
    st.subheader("Download barcode files per arm")
    for arm in barcode_df['Arm'].unique():
        arm_df = barcode_df[barcode_df['Arm']==arm]
        excel_buffer = BytesIO()
        arm_df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button(
            label=f"Download {arm}_barcodes.xlsx",
            data=excel_buffer,
            file_name=f"{arm}_barcodes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.subheader("Download all barcode files as a ZIP")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for arm in barcode_df['Arm'].unique():
            arm_df = barcode_df[barcode_df['Arm']==arm]
            arm_bytes = BytesIO()
            arm_df.to_excel(arm_bytes, index=False)
            arm_bytes.seek(0)
            zip_file.writestr(f"{arm}_barcodes.xlsx", arm_bytes.read())
    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download All Barcode Files (ZIP)",
        data=zip_buffer,
        file_name="all_barcodes.zip",
        mime="application/zip"
    ) 
        
        
