import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import base64

# --- APP CONFIGURATION ---
st.set_page_config(page_title="MVS Supply Point", page_icon="📦", layout="wide")

# --- GOOGLE SHEET CONNECTION ---
# Aap ki sheet ka link yahan automatic set kar diya hai
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tDHHQSs6Gdvcpy7rYcfNvaxJNHoe8ICjyN5YgMizRNg/edit?usp=sharing"

# Streamlit Connection Setup
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Database connection error: {e}")

# Data Load Karne Ke Functions
def load_users():
    try:
        return conn.read(spreadsheet=SHEET_URL, worksheet="users", ttl=0).astype(str)
    except:
        return pd.DataFrame(columns=["name", "username", "role", "pin", "vehicle"])

def load_orders():
    try:
        return conn.read(spreadsheet=SHEET_URL, worksheet="orders", ttl=0).astype(str)
    except:
        return pd.DataFrame(columns=["bill_no", "sku", "qty", "city", "customer", "driver", "dispatched_by", "status", "variance", "bill_image"])

# --- SESSION STATES FOR LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.session_state["user_fullname"] = None
    st.session_state["vehicle"] = None

# --- LOGOUT ---
if st.session_state["logged_in"]:
    if st.sidebar.button("🔓 Logout / Switch Account"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- SECURITY LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.title("🔐 MVS Supply Point - Secure Login")
    st.write("Apna Registered Username aur 4-Digit Security PIN enter kareen.")
    
    username_input = st.text_input("Username").strip()
    pin_input = st.text_input("Security PIN", type="password").strip()
    
    if st.button("Sign In"):
        with st.spinner("PIN Verify ho raha hai..."):
            users_df = load_users()
            # Handle column names strictly as per user sheet casing
            u_col = "User Name" if "User Name" in users_df.columns else "username"
            p_col = "Pin" if "Pin" in users_df.columns else "pin"
            n_col = "Name" if "Name" in users_df.columns else "name"
            r_col = "Role" if "Role" in users_df.columns else "role"
            v_col = "vehicle" if "vehicle" in users_df.columns else "vehicle"
            
            user_match = users_df[(users_df[u_col] == username_input) & (users_df[p_col] == pin_input)]
            
            if not user_match.empty:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = user_match.iloc[0][r_col]
                st.session_state["username"] = user_match.iloc[0][u_col]
                st.session_state["user_fullname"] = user_match.iloc[0][n_col]
                st.session_state["vehicle"] = user_match.iloc[0][v_col]
                st.success(f"Khushamdeed {st.session_state['user_fullname']}!")
                st.rerun()
            else:
                st.error("Ghalat Username ya Security PIN! Dobara koshish kareen.")

# --- AFTER SUCCESSFUL LOGIN ---
else:
    role = st.session_state["user_role"]
    
    # ==========================================
    # 1. ADMIN DASHBOARD
    # ==========================================
    if role == "Admin":
        st.title("👑 MVS Admin Master Dashboard")
        
        tab1, tab2, tab3 = st.tabs(["📊 Live Orders Monitor", "👤 Create Accounts", "⚙️ Manage Employees & PINs"])
        
        with tab1:
            st.subheader("Live Stock Status & Reports")
            orders_df = load_orders()
            if orders_df.empty:
                st.info("Filhal koi orders mojud nahi heen.")
            else:
                st.dataframe(orders_df, use_container_width=True)
                
                # Excel/CSV Export Option
                csv_data = orders_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Full Excel Report", data=csv_data, file_name="MVS_Stock_Report.csv", mime="text/csv")
                
                # Show Uploaded Bill Photos if available
                st.write("### 📷 Uploaded Bills Viewer")
                for idx, row in orders_df.iterrows():
                    if pd.notna(row.get('bill_image')) and str(row['bill_image']).strip() != "":
                        try:
                            with st.expander(f"View Bill Photo - Invoice: {row['bill_no']} ({row['customer']})"):
                                img_bytes = base64.b64decode(row['bill_image'])
                                st.image(img_bytes, width=400)
                        except:
                            pass
                            
        with tab2:
            st.subheader("One-by-One Account Creation (10 Stock Boys / 5 Drivers)")
            users_df = load_users()
            
            new_name = st.text_input("Full Name")
            new_user = st.text_input("Unique Username")
            new_role = st.selectbox("Designation / Role", ["Stock Boy", "Driver"])
            new_pin = st.text_input("Set 4-Digit Secure PIN", max_chars=4, type="password")
            new_veh = st.text_input("Vehicle / Gari Ka Number") if new_role == "Driver" else "N/A"
            
            if st.button("Save & Create Account"):
                u_col = "User Name" if "User Name" in users_df.columns else "username"
                if new_user in users_df[u_col].values:
                    st.error("Ye username pehle se mojud hai! Naya username rakheen.")
                elif len(new_pin) != 4 or not new_pin.isdigit():
                    st.error("PIN sirf 4 hifzon ka hona chahiye!")
                elif not new_name or not new_user:
                    st.error("Sari fields fill karna lazmi hai!")
                else:
                    new_row = {
                        "Name": new_name, "User Name": new_user, "Role": new_role, "Pin": new_pin, "vehicle": new_veh
                    } if "User Name" in users_df.columns else {
                        "name": new_name, "username": new_user, "role": new_role, "pin": new_pin, "vehicle": new_veh
                    }
                    
                    updated_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_df)
                    st.success(f"{new_name} ({new_role}) ka account Google Sheet me save ho gaya!")
                    st.rerun()
                    
        with tab3:
            st.subheader("Employee Security - PIN Reset Section")
            st.write("Agar koi mulazim chor jaye to yahan se foran security code change kareen:")
            users_df = load_users()
            u_col = "User Name" if "User Name" in users_df.columns else "username"
            p_col = "Pin" if "Pin" in users_df.columns else "pin"
            n_col = "Name" if "Name" in users_df.columns else "name"
            r_col = "Role" if "Role" in users_df.columns else "role"
            
            for index, row in users_df.iterrows():
                if row[r_col] != "Admin":
                    col1, col2, col3 = st.columns([2, 2, 1])
                    col1.write(f"👤 **{row[n_col]}** ({row[r_col]}) - User: {row[u_col]}")
                    new_ep_pin = col2.text_input(f"New PIN for {row[u_col]}", max_chars=4, key=f"pin_{row[u_col]}")
                    
                    if col3.button("Update Code", key=f"btn_{row[u_col]}"):
                        if len(new_ep_pin) == 4 and new_ep_pin.isdigit():
                            users_df.at[index, p_col] = new_ep_pin
                            conn.update(spreadsheet=SHEET_URL, worksheet="users", data=users_df)
                            st.success(f"{row[n_col]} ka code successfully change ho gaya!")
                            st.rerun()
                        else:
                            st.error("PIN 4 numbers ka hona chahiye.")

    # ==========================================
    # 2. STOCK BOY PANEL
    # ==========================================
    elif role == "Stock Boy":
        st.title("📦 MVS Stock Boy - Dispatch Section")
        st.write(f"Dispatcher: **{st.session_state['user_fullname']}**")
        
        users_df = load_users()
        r_col = "Role" if "Role" in users_df.columns else "role"
        n_col = "Name" if "Name" in users_df.columns else "name"
        v_col = "vehicle" if "vehicle" in users_df.columns else "vehicle"
        
        drivers_list = users_df[users_df[r_col] == "Driver"]
        driver_options = [f"{row[n_col]} ({row[v_col]})" for idx, row in drivers_list.iterrows()]
        
        st.subheader("New Dispatch Cargo Entry")
        sel_driver = st.selectbox("Select Target Driver & Vehicle", driver_options if driver_options else ["No Registered Drivers Found"])
        bill_no = st.text_input("Bill / Invoice Number")
        sku = st.text_input("Product SKU / Description")
        qty = st.number_input("Quantity (Tadaad)", min_value=1, step=1)
        city = st.text_input("Destination City / Customer Town")
        customer = st.text_input("Customer Name")
        
        # 📸 Bill Photo Upload Option Added
        uploaded_bill = st.file_uploader("📷 Upload Bill Photo / Delivery Receipt", type=["jpg", "png", "jpeg"])
        bill_img_string = ""
        if uploaded_bill is not None:
            bill_img_string = base64.b64encode(uploaded_bill.read()).decode()
            st.success("Bill ki tasveer upload ho gayi!")

        if st.button("Submit Stock & Notify Admin"):
            if not bill_no or not sku or not city or not customer:
                st.error("Sari maloomat fill karna zaroori hai!")
            else:
                orders_df = load_orders()
                new_order_row = {
