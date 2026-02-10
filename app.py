import streamlit as st
import pandas as pd
import io
import zipfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
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

# --- PDF 1: MASTER SUMMARY (For Troop Leader Only) ---
def create_master_summary_pdf(dataframe, title):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Dynamic Widths
    total_page_width = 10.0 * inch
    name_col_width = 1.5 * inch
    num_cookie_cols = len(dataframe.columns) - 1
    if num_cookie_cols > 0:
        cookie_col_width = (total_page_width - name_col_width) / num_cookie_cols
    else:
        cookie_col_width = 1 * inch
    col_widths = [name_col_width] + [cookie_col_width] * num_cookie_cols

    # Header Styling
    header_style = ParagraphStyle('Header', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.whitesmoke, fontName='Helvetica-Bold')
    
    raw_data = [dataframe.columns.to_list()] + dataframe.values.tolist()
    formatted_data = []
    
    # Headers
    headers = [Paragraph(str(col), header_style) for col in raw_data[0]]
    formatted_data.append(headers)
    formatted_data.extend(raw_data[1:])
    
    t = Table(formatted_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.seagreen),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- PDF 2: INDIVIDUAL SCOUT PACKET (Summary + Slips) ---
def create_scout_packet(girl_name, girl_df, cookie_cols, cust_col):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=portrait(letter),
        leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # --- PAGE 1: PICKUP SUMMARY ---
    elements.append(Paragraph(f"Pickup Order For: {girl_name}", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("This is the total inventory you need to collect from the Troop Leader.", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Calculate Totals
    total_row = girl_df[cookie_cols].sum()
    total_row = total_row[total_row > 0] # Only show what she needs
    
    if total_row.empty:
        elements.append(Paragraph("No cookies needed!", styles['Normal']))
    else:
        # Create a vertical list table for clarity
        data = [["Cookie Type", "Qty"]]
        total_boxes = 0
        for cookie, count in total_row.items():
            data.append([cookie, int(count)])
            total_boxes += int(count)
        data.append(["TOTAL BOXES", total_boxes])

        t = Table(data, colWidths=[3*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.seagreen),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), # Total Row
        ]))
        elements.append(t)

    # --- PAGE 2+: CUSTOMER SLIPS ---
    elements.append(PageBreak())
    
    slip_header = ParagraphStyle('SlipHeader', parent=styles['Heading3'], fontSize=12, spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10)
    
    elements.append(Paragraph(f"Customer Packing Slips: {girl_name}", styles['Title']))
    elements.append(Paragraph("Cut these out and tape them to your delivery bags.", styles['Normal']))
    elements.append(Spacer(1, 20))

    for index, row in girl_df.iterrows():
        content = []
        customer_name = row[cust_col] if cust_col in girl_df.columns else "Unknown Customer"
        
        content.append(Paragraph(f"Customer: <b>{customer_name}</b>", slip_header))
        content.append(Spacer(1, 4))
        
        order_data = []
        total_boxes = 0
        for col in cookie_cols:
            count = row[col]
            if count > 0:
                order_data.append([col, int(count)])
                total_boxes += int(count)
        
        if order_data:
            order_data.append(["TOTAL BOXES", total_boxes])
            t = Table(order_data, colWidths=[3.5*inch, 1*inch])
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
        
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MAIN APP ---
st.set_page_config(page_title="Troop Cookie Logistics", layout="wide", page_icon="🍪")
st.title("🍪 Cookie Logistics Manager")

c1, c2 = st.columns(2)
with c1:
    st.markdown("### 🛑 The Problem\nThe \"Digital Cookie\" website gives you a messy spreadsheet, forcing you to hand-count \"Girl Delivery\" orders.")
with c2:
    st.markdown("### ✅ The Solution\nUpload that raw spreadsheet here. This tool filters for \"Girl Delivery\" and generates individual PDF packets for each Scout.")

st.warning("**⚠️ IMPORTANT:** This tool ONLY counts Digital Orders marked for 'Girl Delivery'. It EXCLUDES Shipped/Donated orders and Paper Card orders.")

uploaded_file = st.file_uploader("📂 Upload 'All Orders' CSV", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # Load & Clean
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)
        
        # Filter Delivery
        delivery_cols = [c for c in df.columns if "delivery" in c.lower() or "order type" in c.lower()]
        if not delivery_cols: st.stop()
        df_delivery = df[df[delivery_cols[0]].astype(str).str.contains("Girl|In-Person", case=False, na=False)].copy()
        
        st.success(f"✅ Processing **{len(df_delivery)}** Girl Delivery orders.")

        # Identify Cookies
        found_cookie_cols = []
        rename_map = {}
        for clean, subs in KNOWN_COOKIES.items():
            for sub in subs:
                matches = [c for c in df.columns if sub.lower() in c.lower()]
                for m in matches:
                    if m not in found_cookie_cols:
                        found_cookie_cols.append(m)
                        rename_map[m] = clean
        df_delivery[found_cookie_cols] = df_delivery[found_cookie_cols].fillna(0)
        
        # Identify Names/Customers
        girl_cols = [c for c in df.columns if "girl" in c.lower() and "name" in c.lower()]
        girl_col = girl_cols[0] if girl_cols else df_delivery.index.name
        cust_cols = [c for c in df.columns if "customer" in c.lower()]
        cust_col = cust_cols[0] if cust_cols else "Customer"

        # --- UI TABS ---
        tab1, tab2 = st.tabs(["📦 Troop Master List", "✉️ Scout Packets"])

        # TAB 1: MASTER LIST
        with tab1:
            st.subheader("Master Inventory Pull List (Troop Leader Only)")
            pivot = df_delivery.groupby(girl_col)[found_cookie_cols].sum()
            pivot = pivot.rename(columns=rename_map)
            pivot = pivot[pivot.sum(axis=1) > 0]
            st.dataframe(pivot)
            
            # Download Master PDF
            pdf_master = create_master_summary_pdf(pivot.reset_index(), "Master Troop Pull List")
            st.download_button("📄 Download Master List (PDF)", data=pdf_master, file_name="Master_Pull_List.pdf", mime="application/pdf")

        # TAB 2: INDIVIDUAL PACKETS
        with tab2:
            st.subheader("Individual Scout Packets")
            st.markdown("Download a ZIP file containing separate PDFs for each girl. Email these directly to parents.")
            
            if girl_col:
                # Create ZIP in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    unique_girls = df_delivery[girl_col].unique()
                    
                    progress_bar = st.progress(0)
                    for i, girl in enumerate(unique_girls):
                        # Filter data for this girl
                        girl_df = df_delivery[df_delivery[girl_col] == girl]
                        
                        # Generate her PDF
                        pdf_bytes = create_scout_packet(girl, girl_df, found_cookie_cols, cust_col)
                        
                        # Add to ZIP
                        clean_name = "".join(x for x in str(girl) if x.isalnum() or x in " _-")
                        zf.writestr(f"{clean_name}_Cookie_Packet.pdf", pdf_bytes.getvalue())
                        
                        progress_bar.progress((i + 1) / len(unique_girls))
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="📦 Download All Scout Packets (ZIP)",
                    data=zip_buffer,
                    file_name="Scout_Cookie_Packets.zip",
                    mime="application/zip",
                    type="primary"
                )
                st.success(f"Ready to download packets for {len(unique_girls)} scouts!")

    except Exception as e:
        st.error(f"Error: {e}")
