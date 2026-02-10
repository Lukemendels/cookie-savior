import streamlit as st
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURATION ---
KNOWN_COOKIES = {
    "Adventurefuls": ["Adventurefuls"],
    "Toast-Yay!": ["Toast-Yay"],
    "Lemon-Ups": ["Lemon-Ups", "Lemonades"],
    "Trefoils": ["Trefoils", "Shortbread"],
    "Do-si-dos": ["Do-si-dos", "Peanut Butter Sandwich"],
    "Samoas": ["Samoas", "Caramel deLites"],
    "Tagalongs": ["Tagalongs", "Peanut Butter Patties"],
    "Thin Mints": ["Thin Mints"],
    "Girl Scout S'mores": ["S'mores", "Smores"],
    "Toffee-tastic": ["Toffee-tastic", "Caramel Chocolate Chip"],
    "Gluten Free": ["Gluten Free"],
}

def create_pdf(dataframe, title):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Data Prep
    data = [dataframe.columns.to_list()] + dataframe.values.tolist()
    t = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.seagreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Troop Cookie Logistics", layout="wide")
st.title("🍪 Troop Cookie Logistics Manager")

uploaded_file = st.file_uploader("Upload Digital Cookie CSV Export", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        clean_cols = {c: c.strip() for c in df.columns}
        df.rename(columns=clean_cols, inplace=True)
        
        # Filter for Delivery
        delivery_cols = [c for c in df.columns if "delivery" in c.lower() or "order type" in c.lower()]
        if not delivery_cols:
            st.error("Column error: Could not find 'Delivery Method' or 'Order Type'.")
            st.stop()
            
        target_col = delivery_cols[0]
        delivery_mask = df[target_col].astype(str).str.contains("Girl|In-Person", case=False, na=False)
        df_delivery = df[delivery_mask].copy()
        
        # Identify Cookies
        found_cookie_cols = []
        rename_map = {}
        for clean_name, subtitles in KNOWN_COOKIES.items():
            for sub in subtitles:
                matches = [c for c in df.columns if sub.lower() in c.lower()]
                for match in matches:
                    if match not in found_cookie_cols:
                        found_cookie_cols.append(match)
                        rename_map[match] = clean_name
        
        if not found_cookie_cols:
            st.error("No cookie columns found!")
            st.stop()

        df_delivery[found_cookie_cols] = df_delivery[found_cookie_cols].fillna(0)

        # Tab 1: Master List
        st.header("📦 Master Inventory Pull List")
        total_needed = df_delivery[found_cookie_cols].sum().rename(index=rename_map)
        total_needed = total_needed[total_needed > 0].sort_values(ascending=False)
        st.dataframe(total_needed)

        # Tab 2: Pick List
        st.header("👧 Per-Girl Pick List")
        name_cols = [c for c in df.columns if "girl" in c.lower() and "name" in c.lower()]
        grouper = name_cols[0] if name_cols else df_delivery.index
        
        pivot = df_delivery.groupby(grouper)[found_cookie_cols].sum()
        pivot = pivot.rename(columns=rename_map)
        pivot = pivot[pivot.sum(axis=1) > 0]
        st.dataframe(pivot)

        # PDF Download
        st.divider()
        pdf_file = create_pdf(pivot.reset_index(), "Girl Scout Cookie Pick List") 
        st.download_button("📄 Download PDF Pick List", data=pdf_file, file_name="Pick_List.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error: {e}")
