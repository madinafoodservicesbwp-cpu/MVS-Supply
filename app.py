import streamlit as st
import pandas as pd
import os

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Warehouse Logistics System", page_icon="📦", layout="wide")

# --- INITIALIZE DATABASE FILES ---
if not os.path.exists("users.csv"):
    df_users = pd.DataFrame([
        {"name": "Super Admin", "username": "admin", "role": "Admin", "pin": "1122", "vehicle": "N/A"},
        {"name": "Ali Stock", "username": "ali11", "role": "Stock Boy", "pin": "3344", "vehicle": "N/A"},
        {"name": "Asif Driver", "username": "asif22", "role": "Driver", "pin": "5566", "vehicle": "LES-1234"}
    ])
    df_users.to_csv("users.csv", index=False)

if not os.path.exists("orders.csv"):
    df_orders = pd.DataFrame(columns=["bill_no", "sku", "qty", "city", "customer", "driver", "dispatched_by", "status", "variance"])
    df_orders.to_csv("orders.csv", index=False)

def get_users(): return pd.read_csv("users.csv", dtype=str)
def save_users(df): df.to_csv("users.csv", index=False)
def get_orders(): return pd.read_csv("orders.csv", dtype=str)
def save_orders(df): df.to_csv("orders.csv", index=False)

# --- SESSION STATES FOR LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.session_state["user_fullname"] = None
    st.session_state["vehicle"] = None

# --- LOGOUT BUTTON ---
if st.session_state["logged_in"]:
    if st.sidebar.button("🔓 Logout / Switch Account"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()

# --- LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.title("🔐 Shahzoor Warehouse Secure Login")
    st.write("Apna Username aur 4-Digit Security PIN enter kareen.")
    
    username_input = st.text_input("Username").strip()
    pin_input = st.text_input("Security PIN", type="password").strip()
    
    if st.button("Sign In"):
        users = get_users()
        user_match = users[(users["username"] == username_input) & (users["pin"] == pin_input)]
        
        if not user_match.empty:
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = user_match.iloc[0]["role"]
            st.session_state["username"] = user_match.iloc[0]["username"]
            st.session_state["user_fullname"] = user_match.iloc[0]["name"]
            st.session_state["vehicle"] = user_match.iloc[0]["vehicle"]
            st.success(f"Khushamdeed {st.session_state['user_fullname']}!")
            st.rerun()
        else:
            st.error("Ghalat Username ya Security PIN! Dobara koshish kareen.")

# --- MAIN SECTIONS BASED ON ROLE ---
else:
    role = st.session_state["user_role"]
    
    # 1. ADMIN PANEL
    if role == "Admin":
        st.title("👑 Admin Master Dashboard")
        tab1, tab2, tab3 = st.tabs(["📊 Live Orders Monitor", "👤 Create Accounts", "⚙️ Manage Employees & PINs"])
        
        with tab1:
            st.subheader("Live Stock Status & Notifications")
            orders = get_orders()
            if orders.empty:
                st.info("Filhal koi orders mojud nahi heen.")
            else:
                st.dataframe(orders, use_container_width=True)
                
        with tab2:
            st.subheader("One-by-One Account Creation (10 Stock Boys / 5 Drivers)")
            new_name = st.text_input("Full Name")
            new_username = st.text_input("Unique Username")
            new_role = st.selectbox("Select Role", ["Stock Boy", "Driver"])
            new_pin = st.text_input("Set 4-Digit PIN", max_chars=4, type="password")
            new_vehicle = st.text_input("Vehicle / Gari Ka Number") if new_role == "Driver" else "N/A"
            
            if st.button("Create Account"):
                users = get_users()
                if new_username in users["username"].values:
                    st.error("Ye username pehle se mojud hai!")
                elif len(new_pin) != 4:
                    st.error("PIN 4 numbers ka hona chahiye!")
                else:
                    new_user = pd.DataFrame([{"name": new_name, "username": new_username, "role": new_role, "pin": new_pin, "vehicle": new_vehicle}])
                    users = pd.concat([users, new_user], ignore_index=True)
                    save_users(users)
                    st.success(f"{new_role} ka account kamyabi se ban gaya!")
                    st.rerun()
                    
        with tab3:
            st.subheader("Employee Security & PIN Change Section")
            users = get_users()
            for index, row in users.iterrows():
                if row["role"] != "Admin":
                    col1, col2, col3 = st.columns([2, 2, 2])
                    col1.write(f"**{row['name']}** ({row['role']})")
                    new_employee_pin = col2.text_input(f"New PIN for {row['username']}", max_chars=4, key=f"pin_{row['username']}")
                    if col3.button("Update PIN", key=f"btn_{row['username']}"):
                        if len(new_employee_pin) == 4:
                            users.at[index, "pin"] = new_employee_pin
                            save_users(users)
                            st.success(f"{row['name']} ka PIN code update ho gaya!")
                            st.rerun()

    # 2. STOCK BOY PANEL
    elif role == "Stock Boy":
        st.title(f"📦 Stock Boy Section - Entry Portal")
        users = get_users()
        drivers_list = users[users["role"] == "Driver"]
        driver_options = [f"{row['name']} ({row['vehicle']})" for idx, row in drivers_list.iterrows()]
        
        st.subheader("Add Stock Dispatch Details")
        selected_driver = st.selectbox("Select Target Driver & Vehicle", driver_options)
        bill_no = st.text_input("Bill / Invoice Number")
        sku = st.text_input("Product SKU / Code")
        qty = st.number_input("Quantity (Tadaad)", min_value=1, step=1)
        city = st.text_input("Destination City / Shehar")
        customer = st.text_input("Customer Name")
        
        if st.button("Submit Stock to Driver & Notify Admin"):
            orders = get_orders()
            new_order = pd.DataFrame([{
                "bill_no": bill_no, "sku": sku, "qty": str(qty), "city": city, "customer": customer,
                "driver": selected_driver, "dispatched_by": st.session_state['user_fullname'],
                "status": "Out for Delivery", "variance": "Pending at City"
            }])
            orders = pd.concat([orders, new_order], ignore_index=True)
            save_orders(orders)
            st.success("Stock Driver ke hawale ho gaya aur Admin ko notification chali gayi!")

    # 3. DRIVER PANEL
    elif role == "Driver":
        st.title(f"🚛 Driver Section - Delivery Portal")
        orders = get_orders()
        my_orders = orders[orders["driver"].str.contains(st.session_state['user_fullname'], na=False)]
        
        if my_orders.empty:
            st.info("Aap ke naam filhal koi stock assigned nahi hai.")
        else:
            for index, row in my_orders.iterrows():
                st.write(f"---")
                st.write(f"📍 **City:** {row['city']} | **Customer:** {row['customer']} | **Bill No:** {row['bill_no']}")
                st.write(f"📦 SKU: {row['sku']} | Qty: {row['qty']} | Status: **{row['status']}** ({row['variance']})")
                
                if row["status"] != "Delivered":
                    col1, col2, col3 = st.columns(3)
                    if col1.button("✅ Delivered OK", key=f"ok_{index}"):
                        orders.at[index, "status"] = "Delivered"
                        orders.at[index, "variance"] = "Normal Delivery"
                        save_orders(orders)
                        st.rerun()
                    if col2.button("⚠️ Stock Short", key=f"sh_{index}"):
                        orders.at[index, "status"] = "Delivered"
                        orders.at[index, "variance"] = "Stock Short"
                        save_orders(orders)
                        st.rerun()
                    if col3.button("➕ Stock Extra", key=f"ex_{index}"):
                        orders.at[index, "status"] = "Delivered"
                        orders.at[index, "variance"] = "Stock Extra"
                        save_orders(orders)
                        st.rerun()
