# 🍪 Cookie Logistics Manager (The "Cookie Savior")

**Stop counting boxes by hand. Start delivering.**

This tool automates the chaotic "Girl Delivery" logistics for Girl Scout Cookie season. It takes the raw, messy CSV export from **Digital Cookie** and turns it into clean, printable pick lists and packing slips.

## 🛑 The Problem
The standard Digital Cookie export is a row-by-row transaction log. To figure out what a specific Scout needs to pick up from the Troop Leader, you have to:
1. Filter out "Shipped" and "Donated" orders.
2. Sum up the rows for that specific girl.
3. Manually write it down.
If a girl has 50 orders, that is 50 chances to make a math error.

## ✅ The Solution
This Streamlit app does the math for you.
* **Baker Agnostic:** Works for **Little Brownie Bakers (LBB)** (Samoas/Trefoils) AND **ABC Bakers** (Caramel deLites/Shortbread).
* **Smart Filtering:** Automatically isolates "Girl Delivery" orders so you don't track inventory that is being shipped by the warehouse.
* **PDF Generation:** Instantly creates:
    * **Master Pull List:** For the Troop Leader to pull inventory from the cupboard.
    * **Scout Packets:** A ZIP file containing individual PDFs for each girl (Summary + Packing Slips).

## 🚀 How to Use (For Troop Leaders)
1.  **Log in** to [Digital Cookie](https://digitalcookie.girlscouts.org/).
2.  Navigate to the **Orders** tab.
3.  Scroll to the bottom and click **"Export Orders"** (Save the `.csv` or `.xlsx` file).
4.  Open the **Cookie Logistics Manager** app.
5.  Drag and drop your file.
6.  Download your PDFs!

## 🔒 Privacy & Security
* **In-Memory Processing:** Your data is processed in the system's RAM and is **never saved** to a database or disk.
* **Ephemeral:** Once you close the browser tab, the data is wiped instantly.
* **No Tracking:** We do not store email addresses, scout names, or customer data.

## 💻 Running Locally (For Developers)
If you prefer to run this on your own machine instead of the web:

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/Lukemendels/cookie-savior.git](https://github.com/Lukemendels/cookie-savior.git)
    cd cookie-savior
    ```

2.  **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app:**
    ```bash
    streamlit run app.py
    ```

## ⚠️ Disclaimer
This is a volunteer project built by a Girl Scout Dad. It is not officially affiliated with, endorsed by, or supported by Girl Scouts of the USA (GSUSA). Always verify your totals before placing irrevocable orders!

---
*Built with ❤️ by Luke M.*
