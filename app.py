import streamlit as st
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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

# --- PDF GENERATOR 1: MASTER SUMMARY ---
def create_summary_pdf(dataframe, title):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Data Prep
    data = [dataframe.columns.to_list()] + dataframe.values.tolist()
    
    # Auto-adjust column widths if possible, otherwise let ReportLab calculate
    t = Table(data)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.seagreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    t.setStyle(style)
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- PDF GENERATOR 2: PACKING SLIPS ---
def create_packing_slips_pdf(df, cookie_cols):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=portrait(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    slip_header = ParagraphStyle('SlipHeader', parent=styles['Heading3'], fontSize=12, spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10)
    
    # Find Columns
    girl_cols = [c for c in df.columns if "girl" in c.lower() and "name" in c.lower()]
    girl_col = girl_cols[0] if girl_cols else None
    
    cust_cols = [c for c in df.columns if "customer" in c.lower()]
    cust_col = cust_cols[0] if cust_cols else "Customer"

    if girl_col:
        girls = df[girl_col].unique()
        for girl in girls:
            elements.append(Paragraph(f"PACKING SLIPS FOR: {girl}", styles['Title']))
            elements.append(Spacer(1, 12))
            
            girl_orders = df[df[girl_col] == girl]
            
            for index, row in girl_orders.iterrows():
                content = []
                customer_name = row[cust_col] if cust_col in df.columns else "Unknown Customer"
                
                # Header
                content.append(Paragraph(f"Customer: <b>{customer_name}</b>", slip_header))
                content.append(Spacer(1, 4))
                
                # Table Data
                order_data = []
                total_boxes = 0
                for col in cookie_cols:
                    count = row[col]
                    if count > 0:
                        order_data.append([col, int(count)])
                        total_boxes += int(count)
                
                if order_data:
                    order_data.append(["TOTAL BOXES", total_boxes])
                    t = Table(order_data, colWidths=[3*inch, 1*inch])
                    t.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ]))
                    content.append(t)
                
                content.append(Spacer(1, 15))
                content.append(Paragraph("- - - - - - - - - CUT HERE - - - - - - - - -", normal_style))
                content.append(Spacer(1, 15))

                elements.append(KeepTogether(content))

            elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MAIN APP UI ---
st.set_page_config(page_title="Troop Cookie Logistics", layout="wide", page_icon="🍪")

# HEADER & INSTRUCTIONS
st.title("🍪 Cookie Logistics Manager")
st.markdown("### Stop counting by hand. Start delivering.")

with st.expander("ℹ️ **How to use this tool (Click to expand)**", expanded=True):
    st.markdown("""
    1.  **Log in to Digital Cookie** and go to the **Orders** tab.
    2.  Scroll to the bottom and click **"Export Orders"** (Save the CSV file).
    3.  **Upload that file below.**
    4.  This tool will automatically:
        * Filter for **"Girl Delivery"** orders only (ignoring Shipped/Donated).
        * Calculate the exact boxes you need to give each Scout.
        * Generate printable **Packing Slips** for parents to tape to bags.
    """)

st.info("🔒 **Privacy Note:** This tool processes your file in-memory. No data is saved, stored, or shared. Once you close this tab, the data is gone.")

# FILE UPLOADER
uploaded_file = st.file_uploader("📂 Upload your 'All Orders' CSV export here", type=['csv', 'xlsx'])

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
            st.error("❌ **Error:** Could not find 'Delivery Method' or 'Order Type' column. Please check the CSV.")
            st.stop()
            
        target_col = delivery_cols[0]
        delivery_mask = df[target_col].astype(str).str.contains("Girl|In-Person", case=False, na=False)
        df_delivery = df[delivery_mask].copy()
        
        st.success(f"✅ Found **{len(df_delivery)}** Girl Delivery orders!")

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
            st.error("❌ **Error:** No cookie columns found! Are you sure this is the right file?")
            st.stop()

        df_delivery[found_cookie_cols] = df_delivery[found_cookie_cols].fillna(0)

        # Money Logic
        money_col = None
        possible_money = [c for c in df_delivery.columns if "amount" in c.lower() or "total" in c.lower()]
        if possible_money:
            money_col = possible_money[0]
            # Clean currency string to float
            if df_delivery[money_col].dtype == object:
                df_delivery[money_col] = df_delivery[money_col].astype(str).str.replace('$', '').str.replace(',', '').astype(float)

        # --- TABS ---
        tab1, tab2 = st.tabs(["📦 Troop Master List", "👧 Scout Pick Lists"])

        with tab1:
            st.subheader("Master Inventory Pull List")
            st.markdown("*Use this to pull cases from the Troop Cupboard.*")
            
            # Pivot 1: Total needed by Troop
            total_needed = df_delivery[found_cookie_cols].sum().rename(index=rename_map)
            total_needed = total_needed[total_needed > 0].sort_values(ascending=False)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(total_needed, height=400)
            with c2:
                st.metric("Total Boxes to Move", int(total_needed.sum()))
                if money_col:
                    total_val = df_delivery[money_col].sum()
                    st.metric("Total Digital Value", f"${total_val:,.2f}")

        with tab2:
            st.subheader("Per-Girl Pick List")
            st.markdown("*Use this to distribute cookies to parents.*")
            
            name_cols = [c for c in df.columns if "girl" in c.lower() and "name" in c.lower()]
            grouper = name_cols[0] if name_cols else df_delivery.index
            
            pivot = df_delivery.groupby(grouper)[found_cookie_cols].sum()
            
            # Add Money to Pivot
            if money_col:
                 money_pivot = df_delivery.groupby(grouper)[money_col].sum()
                 pivot["TOTAL VALUE ($)"] = money_pivot.apply(lambda x: f"${x:,.2f}")

            pivot = pivot.rename(columns=rename_map)
            # Filter rows with 0 boxes
            # (Note: we use numeric_only=True to ignore the string formatted money column for the sum check)
            pivot = pivot[pivot[list(rename_map.values())].sum(axis=1) > 0]
            
            st.dataframe(pivot, use_container_width=True)

        # --- DOWNLOADS ---
        st.divider()
        st.subheader("🖨️ Print & Go")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.info("For the Troop Leader")
            pdf_summary = create_summary_pdf(pivot.reset_index(), "Girl Scout Cookie Pick List") 
            st.download_button("📄 Download Master Pick List (PDF)", data=pdf_summary, file_name="Master_Pick_List.pdf", mime="application/pdf")

        with c2:
            st.info("For the Parents")
            pdf_slips = create_packing_slips_pdf(df_delivery, found_cookie_cols)
            st.download_button("✂️ Download Customer Packing Slips (PDF)", data=pdf_slips, file_name="Customer_Packing_Slips.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"An error occurred: {e}")
