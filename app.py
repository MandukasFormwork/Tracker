import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Mandukas Stock Loop Tracker", page_icon="🏗️", layout="wide")
st.title("🏗️ Mandukas Stock Loop Tracker")
st.markdown("### Physical Logbook Matching & Site Allocation System")

# --- INITIALIZE DATABASE ---
if "locations" not in st.session_state:
    st.session_state.locations = ["Durban Yard", "Joburg Yard", "Umhlanga Ridge Project", "Ballito Junction Site", "Sandton Mall Job"]

if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = ["Kwikstage Standards 3.0m", "Kwikstage Ledgers 2.5m", "Steel Props Size 2", "H20 Timber Beams", "Formwork Plywood Boards"]

if "transfer_ledger" not in st.session_state:
    # Seed historic entries mapping directly to physical paper sequences
    st.session_state.transfer_ledger = pd.DataFrame([
        {"Date & Time": "2026-11-05 08:30", "Doc Type": "HD (Hire Delivery)", "Ref Number": "HD-9821", "From": "Durban Yard", "To": "Umhlanga Ridge Project", "Item": "Steel Props Size 2", "Qty": 450, "Driver/Manager": "A. Khumalo"},
        {"Date & Time": "2026-11-05 14:15", "Doc Type": "HR (Hire Return)", "Ref Number": "HR-4402", "From": "Sandton Mall Job", "To": "Joburg Yard", "Item": "Kwikstage Standards 3.0m", "Qty": 150, "Driver/Manager": "J. Botha"},
        {"Date & Time": "2026-11-06 10:00", "Doc Type": "TRF (Transfer Note)", "Ref Number": "TRF-0911", "From": "Umhlanga Ridge Project", "To": "Ballito Junction Site", "Item": "H20 Timber Beams", "Qty": 120, "Driver/Manager": "S. Govender"}
    ])

# --- STOCK CALCULATION LOGIC ---
def get_site_balance(location, item):
    ledger = pd.DataFrame(st.session_state.transfer_ledger)
    if ledger.empty:
        return 0
    total_in = ledger[(ledger["To"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    total_out = ledger[(ledger["From"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    # Base reserve assumptions for main yards
    initial_stock = 10000 if "Yard" in location else 0
    return (initial_stock + total_in) - total_out

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Live Site Stock Levels", "📝 Record Paper Book Note", "➕ Register New Projects/Yards"])

# ==========================================
# TAB 1: LIVE SITE BALANCES
# ==========================================
with tab1:
    st.header("📊 Current Stock On-Site")
    selected_location = st.selectbox("Select Yard or Construction Site to Inspect:", st.session_state.locations)
    
    balances = []
    for item in st.session_state.inventory_items:
        current_bal = get_site_balance(selected_location, item)
        balances.append({"Equipment Item": item, "Current Balance On-Site": current_bal})
    
    st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)

# ==========================================
# TAB 2: LOGBOOK ROUTING ENGINE
# ==========================================
with tab2:
    st.header("📝 New Logbook Entry")
    st.markdown("Capture raw dispatch, return, or site-to-site movement records directly from physical tracking books.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type = st.selectbox("Select Logbook Document Type:", ["HD (Hire Delivery)", "HR (Hire Return)", "TRF (Transfer Note)"])
    with col2:
        ref_number = st.text_input("Physical Note Reference Number:", placeholder="e.g., HD-9942, HR-1105")
    with col3:
        driver_auth = st.text_input("Driver Name / Yard Manager Initial:")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        from_loc = st.selectbox("Source (From):", st.session_state.locations, key="src")
    with col5:
        dest_options = [loc for loc in st.session_state.locations if loc != from_loc]
        to_loc = st.selectbox("Destination (To):", dest_options, key="dest")
    with col6:
        selected_item = st.selectbox("Select Material Type:", st.session_state.inventory_items)

    qty = st.number_input("Count of Physical Units:", min_value=1, value=50, step=1)
    
    if st.button("Log Document Entry", type="primary"):
        if not ref_number.strip():
            st.error("Transaction rejected! You must supply a valid Reference Number from the physical logbook.")
        else:
            # Enforce stock verification for project-to-project allocations
            available_stock = get_site_balance(from_loc, selected_item)
            if "Yard" not in from_loc and qty > available_stock:
                st.error(f"Deficit Blocked! '{from_loc}' only holds {available_stock} units of {selected_item}. You cannot move {qty}.")
            else:
                new_entry = {
                    "Date & Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Doc Type": doc_type,
                    "Ref Number": ref_number.strip().upper(),
                    "From": from_loc,
                    "To": to_loc,
                    "Item": selected_item,
                    "Qty": int(qty),
                    "Driver/Manager": driver_auth.strip() if driver_auth.strip() else "System Auto"
                }
                
                st.session_state.transfer_ledger = pd.concat([
                    pd.DataFrame([new_entry]), 
                    st.session_state.transfer_ledger
                ], ignore_index=True)
                
                st.success(f"Logged Successfully: {qty} units of {selected_item} recorded via reference {ref_number.upper()}.")

    st.markdown("---")
    st.subheader("📋 Central Movement Ledger Log")
    st.dataframe(st.session_state.transfer_ledger, use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: LOCATION REGISTRY
# ==========================================
with tab3:
    st.header("➕ Expand Tracking Network")
    new_site = st.text_input("Create New Site / Yard Name:")
    if st.button("Add Location to Registry"):
        if new_site.strip() and new_site.strip() not in st.session_state.locations:
            st.session_state.locations.append(new_site.strip())
            st.success(f"'{new_site.strip()}' added to your tracking map.")
        else:
            st.error("Invalid or duplicate location name.")
