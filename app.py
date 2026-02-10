import streamlit as st
import pandas as pd
import io
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

# --- PDF GENERATOR 1: MASTER SUMMARY ---
def create_summary_pdf(dataframe, title):
    buffer = io.BytesIO()
    # Landscape Letter = 11 inches wide. 
    # Margins 0.5 each side -> 10 inches usable width.
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # --- DYNAMIC COLUMN SIZING ---
    # We have 10 inches of width.
    # Name Column: Give it 1.5 inches (plenty for "Rosemary").
    # Cookie Columns: Divide the remaining 8.5 inches by the number of cookies.
    
    total_page_width = 10.0 * inch
    name_col_width = 1.5 * inch
    
    num_cookie_cols = len(dataframe.columns) - 1 # Subtract Name column
    if num_cookie_cols > 0:
        remaining_width = total_page_width - name_col_width
        cookie_col_width = remaining_width / num_cookie_cols
    else:
        cookie_col_width = 1 * inch # Fallback
        
    col_widths = [name_col_width] + [cookie_col_width] * num_cookie_cols

    # --- HEADER FORMATTING ---
    # Create a style for headers that centers text and wraps it (fontSize 9 to fit)
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )

    # Convert raw dataframe data to a list of lists
    raw_data = [dataframe.columns.to_list()] + dataframe.values.tolist()
    
    # Process the Header Row: Wrap strings in Paragraphs so they wrap lines
    formatted_data = []
    
    # Headers
    headers = []
    for col_name in raw_data[0]:
        # Wrap header text in Paragraph so it splits lines (e.g. "Adventure-\nfuls")
        headers.append(Paragraph(str(col_name), header_style))
    formatted_data.append(headers)
    
    # Data Rows (Keep as simple strings/numbers for clean look)
    formatted_data.extend(raw_data[1:])
    
    # Create Table with explicit widths
    t = Table(formatted_data, colWidths=col_widths, repeatRows=1)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.seagreen),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),     # Center all data
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),    # Vertically center
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),        # Data font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
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
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=portrait(letter), 
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    slip_header = ParagraphStyle('SlipHeader', parent=styles['Heading3'], fontSize=12, spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10)
    
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
            elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- MAIN APP UI ---
st.set_page_config(page_title="Troop Cookie Logistics", layout="wide", page_icon="🍪")

st.title("🍪 Cookie Logistics Manager")

c1, c2 = st.columns(2)
with c1:
    st.markdown("""
    ### 🛑 The Problem
    The "Digital Cookie" website gives you a messy spreadsheet, forcing you to hand-count "Girl Delivery" orders one by one.
    """)
with c2:
    st.markdown("""
    ### ✅ The Solution
    Upload that raw spreadsheet here. This secure tool will automatically **filter** for "Girl Delivery" orders and **calculate** the exact pick list for each Scout.
    """)

st.divider()

st.warning("""
**⚠️ IMPORTANT NOTE:**
* This tool **ONLY** counts Digital Orders marked for "Girl Delivery."
* It **DOES NOT** include Paper Card orders (you must add those manually).
* It **EXCLUDES** Shipped/Donated orders (the warehouse handles those).
""")

st.subheader("📝 Instructions")
step1, step2, step3 = st.columns(3)
with step1:
    st.info("**Step 1**\n\nLog in to Digital Cookie and go to the **Orders** tab.")
with step2:
    st.info("**Step 2**\n\nScroll to the bottom and click **'Export Orders'** (Save the CSV).")
with step3:
    st.info("**Step 3**\n\n**Upload** that file in the box below.")

uploaded_file = st.file_uploader("📂 Upload your 'All Orders' CSV export here", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        clean_cols = {c: c.strip() for c in df.columns}
        df.rename(columns=clean_cols, inplace=True)
        
        delivery_cols = [c for c in df.columns if "delivery" in c.lower() or "order type" in c.lower()]
        if not delivery_cols:
            st.error("❌ **Error:** Could not find 'Delivery Method' or 'Order Type' column.")
            st.stop()
            
        target_col = delivery_cols[0]
        delivery_mask = df[target_col].astype(str).str.contains("Girl|In-Person", case=False, na=False)
        df_delivery = df[delivery_mask].copy()
        
        st.success(f"✅ Success! Found **{len(df_delivery)}** Girl Delivery orders.")

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
            st.error("❌ **Error:** No cookie columns found!")
            st.stop()

        df_delivery[found_cookie_cols] = df_delivery[found_cookie_cols].fillna(0)

        money_col = None
        possible_money = [c for c in df_delivery.columns if "amount" in c.lower() or "total" in c.lower()]
        if possible_money:
            money_col = possible_money[0]
            if df_delivery[money_col].dtype == object:
                df_delivery[money_col] = df_delivery[money_col].astype(str).str.replace('$', '').str.replace(',', '').astype(float)

        tab1, tab2 = st.tabs(["📦 Troop Master List", "👧 Scout Pick Lists"])

        with tab1:
            st.subheader("Master Inventory Pull List")
            st.markdown("*Use this to pull cases from the Troop Cupboard.*")
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
            
            if money_col:
                 money_pivot = df_delivery.groupby(grouper)[money_col].sum()
                 pivot["TOTAL VALUE ($)"] = money_pivot.apply(lambda x: f"${x:,.2f}")

            pivot = pivot.rename(columns=rename_map)
            pivot = pivot[pivot[list(rename_map.values())].sum(axis=1) > 0]
            st.dataframe(pivot, use_container_width=True)

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
