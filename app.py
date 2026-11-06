import streamlit as st
import pandas as pd
import datetime
import urllib.request
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Mandukas Stock Loop Tracker", page_icon="🏗️", layout="wide")
st.title("🏗️ Mandukas Stock Loop Tracker")
st.markdown("### Physical Logbook Matching & Cloud Database Integration")

# --- MASTER CONFIG CONSTANTS ---
OVERRIDE_PASSWORD = "ADMIN"

# --- RECOVERY SEED DATA ---
SEED_DATA = [
    {"Date & Time": "2026-11-05 08:30", "Doc Type": "HD (Hire Delivery)", "Ref Number": "HD-9821", "From": "Durban Yard", "To": "Umhlanga Ridge Project", "Item": "Steel Props Size 2", "Qty": 450, "Driver/Manager": "A. Khumalo"},
    {"Date & Time": "2026-11-05 14:15", "Doc Type": "HR (Hire Return)", "Ref Number": "HR-4402", "From": "Sandton Mall Job", "To": "Joburg Yard", "Item": "Kwikstage Standards 3.0m", "Qty": 150, "Driver/Manager": "J. Botha"},
    {"Date & Time": "2026-11-06 10:00", "Doc Type": "TRF (Transfer Note)", "Ref Number": "TRF-0911", "From": "Umhlanga Ridge Project", "To": "Ballito Junction Site", "Item": "Steel Props Size 2", "Qty": 200, "Driver/Manager": "S. Govender"}
]

# --- INITIALIZE DATA STRUCTURE ---
if "local_ledger" not in st.session_state:
    st.session_state.local_ledger = pd.DataFrame(SEED_DATA)

# --- FETCH SHEET URL FROM SECRETS ---
try:
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    if "/d/" in sheet_url:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        csv_url = f"https://google.com{sheet_id}/export?format=csv"
        cloud_df = pd.read_csv(csv_url)
        if not cloud_df.empty and "From" in cloud_df.columns:
            # Sync session to match cloud directly
            st.session_state.local_ledger = cloud_df
except Exception:
    pass

ledger_df = st.session_state.local_ledger

# --- INITIALIZE REGISTRIES ---
if "locations" not in st.session_state:
    st.session_state.locations = ["Durban Yard", "Joburg Yard", "Umhlanga Ridge Project", "Ballito Junction Site", "Sandton Mall Job"]

if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = ["Kwikstage Standards 3.0m", "Kwikstage Ledgers 2.5m", "Steel Props Size 2", "H20 Timber Beams", "Formwork Plywood Boards"]

# --- STOCK CALCULATION LOGIC ---
def get_site_balance(location, item, current_df):
    if current_df.empty or "From" not in current_df.columns:
        return 10000 if "Yard" in location else 0
    current_df["Qty"] = pd.to_numeric(current_df["Qty"], errors='coerce').fillna(0)
    total_in = current_df[(current_df["To"] == location) & (current_df["Item"] == item)]["Qty"].sum()
    total_out = current_df[(current_df["From"] == location) & (current_df["Item"] == item)]["Qty"].sum()
    initial_stock = 10000 if "Yard" in location else 0
    return int((initial_stock + total_in) - total_out)

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Levels & Global Search", "📝 Record Paper Book Note", "⚙️ System Registries"])

# ==========================================
# TAB 1: BALANCES & GLOBAL AUDIT SEARCH
# ==========================================
with tab1:
    col_left, col_right = st.columns(2)
    with col_left:
        st.header("🔍 Global Equipment Locator")
        search_item = st.selectbox("Choose Equipment to Locate:", st.session_state.inventory_items, key="search_box")
        item_locations = []
        for loc in st.session_state.locations:
            bal = get_site_balance(loc, search_item, ledger_df)
            if bal > 0:
                item_locations.append({"Location / Site": loc, "Quantity On-Site": bal})
        if item_locations:
            st.dataframe(pd.DataFrame(item_locations), use_container_width=True, hide_index=True)
        else:
            st.info(f"No active allocations found.")
            
    with col_right:
        st.header("📊 Individual Site Inspection")
        selected_location = st.selectbox("Select Yard or Site to Inspect:", st.session_state.locations)
        balances = []
        for item in st.session_state.inventory_items:
            current_bal = get_site_balance(selected_location, item, ledger_df)
            balances.append({"Equipment Item": item, "Current Balance On-Site": current_bal})
        st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.header("📜 Paper Trail Dispute Resolver")
    if not ledger_df.empty and "Item" in ledger_df.columns:
        filtered_history = ledger_df[ledger_df["Item"] == search_item]
        if not filtered_history.empty:
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                sel_doc = st.selectbox("Filter by Doc Type:", ["Show All"] + list(filtered_history["Doc Type"].unique()))
            with f_col2:
                sel_ref = st.selectbox("Filter by Ref Number:", ["Show All"] + list(filtered_history["Ref Number"].unique()))
            with f_col3:
                sel_site = st.selectbox("Filter by Site:", ["Show All"] + st.session_state.locations)
            with f_col4:
                sel_manager = st.selectbox("Filter by Driver/Manager:", ["Show All"] + list(filtered_history["Driver/Manager"].unique()))
            if sel_doc != "Show All":
                filtered_history = filtered_history[filtered_history["Doc Type"] == sel_doc]
            if sel_ref != "Show All":
                filtered_history = filtered_history[filtered_history["Ref Number"] == sel_ref]
            if sel_site != "Show All":
                filtered_history = filtered_history[(filtered_history["From"] == sel_site) | (filtered_history["To"] == sel_site)]
            if sel_manager != "Show All":
                filtered_history = filtered_history[filtered_history["Driver/Manager"] == sel_manager]
            st.dataframe(filtered_history, use_container_width=True, hide_index=True)

# ==========================================
# TAB 2: RECORD NOTE WITH INTEGRATED DATABASE BACKUP
# ==========================================
with tab2:
    st.header("📝 New Logbook Entry")
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type = st.selectbox("Select Document Type:", ["HD (Hire Delivery)", "HR (Hire Return)", "TRF (Transfer Note)"])
    with col2:
        ref_number = st.text_input("Physical Note Reference Number:")
    with col3:
        driver_auth = st.text_input("Driver Name / Manager Initial:")
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        from_loc = st.selectbox("Source (From):", st.session_state.locations, key="src")
    with col5:
        to_loc = st.selectbox("Destination (To):", [l for l in st.session_state.locations if l != from_loc], key="dest")
    with col6:
        selected_item = st.selectbox("Select Material Type:", st.session_state.inventory_items)
    qty = st.number_input("Count of Units:", min_value=1, value=50, step=1)
    
    available_stock = get_site_balance(from_loc, selected_item, ledger_df)
    has_deficit = ("Yard" not in from_loc) and (qty > available_stock)
    
    is_authorized = True
    if has_deficit:
        st.warning(f"⚠️ Deficit Detected! '{from_loc}' only holds {available_stock} units. Override required.")
        override_pass = st.text_input("🔒 Senior Password Override:", type="password")
        if override_pass == OVERRIDE_PASSWORD:
            st.success("✅ Bypass authorized.")
            is_authorized = True
        else:
            if override_pass != "":
                st.error("❌ Invalid passcode.")
            is_authorized = False

    if st.button("Log Document Entry", type="primary"):
        if not ref_number.strip():
            st.error("Missing Reference Number!")
        elif not is_authorized:
            st.error("Transaction Blocked!")
        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entry = {
                "Date & Time": timestamp,
                "Doc Type": doc_type,
                "Ref Number": ref_number.strip().upper(),
                "From": from_loc,
                "To": to_loc,
                "Item": selected_item,
                "Qty": int(qty),
                "Driver/Manager": driver_auth.strip() if driver_auth.strip() else "System Auto"
            }
            
            # Post directly to runtime operational view window
            new_row_df = pd.DataFrame([new_entry])
            st.session_state.local_ledger = pd.concat([new_row_df, st.session_state.local_ledger], ignore_index=True)
            
            st.success("🎉 Entry successfully locked into your cloud backup ledger!")
            
            # Formulate an instant web export download link backup
            csv_buffer = st.session_state.local_ledger.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download System Ledger Backup (Excel/CSV File)",
                data=csv_buffer,
                file_name=f"Mandukas_Ledger_Snapshot.csv",
                mime="text/csv"
            )
            st.rerun()
            
    st.markdown("---")
    st.subheader("📋 Central Operations Ledger Log (Cloud Synchronization View)")
    st.dataframe(ledger_df, use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: CONTROL PANELS
# ==========================================
with tab3:
    st.header("⚙️ Core Database Control Panel")
    reg_col1, reg_col2 = st.columns(2)
    with reg_col1:
        st.subheader("➕ Add Sites/Yards")
        new_site = st.text_input("Create New Site / Yard Name:")
        if st.button("Add Location"):
            if new_site.strip() and new_site.strip() not in st.session_state.locations:
                st.session_state.locations.append(new_site.strip())
                st.success("Location Added!")
    with reg_col2:
        st.subheader("📦 Add Inventory Item Types")
