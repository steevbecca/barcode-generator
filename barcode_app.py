import streamlit as st
import pandas as pd
from io import BytesIO

# ------------------------
# PK timepoints
pk_timepoints_11 = ['P1','P2','P3','P4','P5','P6','P8','P12','P18','P24','P27']
pk_timepoints_8 = ['P1','P2','P3','P4','P6','P12','P18','P24']

# Define arm details
arm_info = {
    'G1': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_11, 'pk_last_day':14, 'pk_first_day':1},
    'G2': {'mid':None, 'last':'EOT',  'pk_times':pk_timepoints_11, 'pk_last_day':7,  'pk_first_day':1},
    'G3': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_11, 'pk_last_day':14, 'pk_first_day':1},
    'G4': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_8,  'pk_last_day':14, 'pk_first_day':1},
    'G5': {'mid':14,'last':'EOT','pk_times':pk_timepoints_8,  'pk_last_day':28, 'pk_first_day':1},
    'G6': {'mid':7, 'last':'EOT', 'pk_times':pk_timepoints_8,  'pk_last_day':14, 'pk_first_day':1},
}

# ------------------------
# Function to generate barcodes for one patient
def generate_barcodes(row):
    barcodes = []
    arm = row['Treatment arm']
    pid = row['ID']
    pk = row['PK'] == 'Yes'
    
    if arm == 'G7':  # skip if arm is G7
        return barcodes
    
    info = arm_info[arm]
    
    # Mid-treatment collection
    if info['mid']:
        for sample in ['Pl','Se']:
            for label_type in ['H','L']:
                barcodes.append(f"{arm}D{info['mid']}.{sample}.{pid}")
    
    # End-of-treatment collection
    for sample in ['Pl','Se','Ur']:
        for label_type in ['H','L']:
            barcodes.append(f"{arm}D{info['last']}.{sample}.{pid}")
    
    # PK collections
    if pk:
        day1 = info['pk_first_day']
        for tp in info['pk_times']:
            for aliquot in range(1,5):
                barcodes.append(f"{arm}D{day1}.{tp}.{aliquot}.{pid}")
        
        day_last = info['pk_last_day']
        for tp in info['pk_times']:
            for aliquot in range(1,5):
                barcodes.append(f"{arm}D{day_last}.{tp}.{aliquot}.{pid}")
    
    return barcodes

# ------------------------
# Streamlit web interface
st.title("Clinical Trial Barcode Generator")
st.write("Upload your raw Excel file to generate barcodes per arm.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        all_barcodes = []
        for _, row in df.iterrows():
            bcs = generate_barcodes(row)
            all_barcodes.extend([(row['Treatment arm'], row['ID'], bc) for bc in bcs])
        
        barcode_df = pd.DataFrame(all_barcodes, columns=['Arm','ID','Barcode'])
        
        # Generate download buttons for each arm
        st.write("✅ Barcodes generated! Download below:")
        for arm in barcode_df['Arm'].unique():
            arm_df = barcode_df[barcode_df['Arm']==arm]
            buffer = BytesIO()
            arm_df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label=f"Download {arm}_barcodes.xlsx",
                data=buffer,
                file_name=f"{arm}_barcodes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error reading file: {e}")