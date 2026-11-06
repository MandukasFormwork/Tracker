import streamlit as st
import pandas as pd
import datetime
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Mandukas Stock Loop Tracker", page_icon="🏗️", layout="wide")
st.title("🏗️ Mandukas Stock Loop Tracker")
st.markdown("### Physical Logbook Matching & Site Allocation System")

# --- MASTER CONFIG CONSTANTS ---
OVERRIDE_PASSWORD = "ADMIN"

# --- INITIALIZE DATABASE REGISTRIES ---
if "locations" not in st.session_state:
    st.session_state.locations = ["Durban Yard", "Joburg Yard", "Umhlanga Ridge Project", "Ballito Junction Site", "Sandton Mall Job"]

if "inventory_items" not in st.session_state:
    st.session_state.inventory_items = ["Kwikstage Standards 3.0m", "Kwikstage Ledgers 2.5m", "Steel Props Size 2", "H20 Timber Beams", "Formwork Plywood Boards"]

if "transfer_ledger" not in st.session_state:
    st.session_state.transfer_ledger = pd.DataFrame([
        {"Date & Time": "2026-11-05 08:30", "Doc Type": "HD (Hire Delivery)", "Ref Number": "HD-9821", "From": "Durban Yard", "To": "Umhlanga Ridge Project", "Item": "Steel Props Size 2", "Qty": 450, "Driver/Manager": "A. Khumalo", "Has Attachment": "❌ No File Attached"},
        {"Date & Time": "2026-11-05 14:15", "Doc Type": "HR (Hire Return)", "Ref Number": "HR-4402", "From": "Sandton Mall Job", "To": "Joburg Yard", "Item": "Kwikstage Standards 3.0m", "Qty": 150, "Driver/Manager": "J. Botha", "Has Attachment": "❌ No File Attached"},
        {"Date & Time": "2026-11-06 10:00", "Doc Type": "TRF (Transfer Note)", "Ref Number": "TRF-0911", "From": "Umhlanga Ridge Project", "To": "Ballito Junction Site", "Item": "Steel Props Size 2", "Qty": 200, "Driver/Manager": "S. Govender", "Has Attachment": "❌ No File Attached"}
    ])

# Vault to hold raw byte streams of images mapped to their Ref Numbers
if "image_vault" not in st.session_state:
    st.session_state.image_vault = {}

# --- STOCK CALCULATION LOGIC ---
def get_site_balance(location, item):
    ledger = pd.DataFrame(st.session_state.transfer_ledger)
    if ledger.empty or "From" not in ledger.columns:
        return 10000 if "Yard" in location else 0
    ledger["Qty"] = pd.to_numeric(ledger["Qty"], errors='coerce').fillna(0)
    total_in = ledger[(ledger["To"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    total_out = ledger[(ledger["From"] == location) & (ledger["Item"] == item)]["Qty"].sum()
    initial_stock = 10000 if "Yard" in location else 0
    return int((initial_stock + total_in) - total_out)

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Levels & Global Search", "📝 Record Paper Book Note", "⚙️ System Registries"])

# ==========================================
# TAB 1: STOCK LEVELS & DRILL-DOWNS WITH PROOF POPPER
# ==========================================
with tab1:
    col_left, col_right = st.columns(2)
    with col_left:
        st.header("🔍 Global Equipment Locator")
        search_item = st.selectbox("Choose Equipment to Locate:", st.session_state.inventory_items, key="search_box")
        item_locations = []
        for loc in st.session_state.locations:
            bal = get_site_balance(loc, search_item)
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
            current_bal = get_site_balance(selected_location, item)
            balances.append({"Equipment Item": item, "Current Balance On-Site": current_bal})
        st.dataframe(pd.DataFrame(balances), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.header("📜 Global Paper Trail Dispute Resolver & Signed Voucher Vault")
    st.markdown("Select any logged book record below to review its details and extract the actual signed copy:")
    
    ledger_df = pd.DataFrame(st.session_state.transfer_ledger)
    if not ledger_df.empty:
        # Render clean scannable operational grid
        st.dataframe(ledger_df, use_container_width=True, hide_index=True)
        
        st.markdown("#### 🔍 Extract Signed Proof Voucher")
        target_view_ref = st.selectbox("Choose Reference Number to look up signed slip:", ["Select Reference"] + list(ledger_df["Ref Number"].unique()))
        
        if target_view_ref != "Select Reference":
            if target_view_ref in st.session_state.image_vault:
                st.success(f"🖼️ Direct Signed Physical Voucher Proof Found for Note: {target_view_ref}")
                st.image(st.session_state.image_vault[target_view_ref], caption=f"Scanned Signature File for Note {target_view_ref}", width=500)
            else:
                st.warning(f"No image attachment was uploaded by the yard manager when Note {target_view_ref} was originally logged.")

# ==========================================
# TAB 2: RECORD NOTE WITH CAMERA ATTACHMENT HUB
# ==========================================
with tab2:
    st.header("📝 Record Physical Logbook Entry")
    status_msg = st.container()

    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type = st.selectbox("Select Document Type:", ["HD (Hire Delivery)", "HR (Hire Return)", "TRF (Transfer Note)"])
    with col2:
        ref_number = st.text_input("Type Paper Book Note Reference #:", value="", placeholder="e.g., HD-6969, TRF-1024", key="raw_ref_box")
    with col3:
        driver_auth = st.text_input("Type Driver Name / Initial:", value="", placeholder="e.g., Ashley, Khumalo", key="raw_auth_box")
        
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        from_loc = st.selectbox("Source (From):", st.session_state.locations, key="src_loc")
    with col5:
        to_loc = st.selectbox("Destination (To):", st.session_state.locations, key="dest_loc")
    with col6:
        selected_item = st.selectbox("Select Material Type:", st.session_state.inventory_items, key="item_loc")
        
    qty = st.number_input("Count of Physical Units:", min_value=1, max_value=100000, value=100, step=50, key="qty_loc")
    override_pass = st.text_input("🔒 Password Override for Negative Balance Bypasses:", type="password", key="pass_loc")
    
    # 📸 BRAND NEW DOCUMENT ATTACHMENT BOX 📸
    st.markdown("#### 📎 Attach Signed Paper Document Evidence")
    uploaded_slip = st.file_uploader("Take phone photo or upload scan of signed logbook page:", type=["jpg", "png", "jpeg"])

    if st.button("Log Document Entry", type="primary", key="submit_action_btn"):
        cleaned_ref = ref_number.strip().upper()
        current_ledger = pd.DataFrame(st.session_state.transfer_ledger)
        
        existing_refs = [str(x).upper() for x in current_ledger["Ref Number"].tolist()]
        is_duplicate = (cleaned_ref in existing_refs) and (cleaned_ref != "")
            
        available_stock = get_site_balance(from_loc, selected_item)
        has_deficit = "Yard" not in from_loc and qty > available_stock
        
        with status_msg:
            if not ref_number.strip():
                st.error("❌ Rejected! Missing Reference Number from the paper book.")
            elif from_loc == to_loc:
                st.error("❌ Format Error! Source and Destination cannot be the same site location.")
            elif is_duplicate:
                st.error(f"❌ Transaction Blocked! Note reference number '{cleaned_ref}' has ALREADY been used and allocated in the system ledger. Moenie n dom POES wees nie!!")
            elif has_deficit and override_pass != OVERRIDE_PASSWORD:
                st.error(f"❌ Blocked! '{from_loc}' only holds {available_stock} units. Senior Password Override required.")
            else:
                with st.spinner("Uploading signed proof voucher and calculating fleet loops..."):
                    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    manager_initial = driver_auth.strip() if driver_auth.strip() else "Yard Ops"
                    
                    has_file_label = "❌ No File Attached"
                    if uploaded_slip is not None:
                        # Store image data binary linked tightly to its reference code
                        st.session_state.image_vault[cleaned_ref] = uploaded_slip.read()
                        has_file_label = "✅ SIGNED PROOF ATTACHED"
                    
                    new_row = pd.DataFrame([{"Date & Time": time_now, "Doc Type": doc_type, "Ref Number": cleaned_ref, "From": from_loc, "To": to_loc, "Item": selected_item, "Qty": int(qty), "Driver/Manager": manager_initial, "Has Attachment": has_file_label}])
                    st.session_state.transfer_ledger = pd.concat([new_row, st.session_state.transfer_ledger], ignore_index=True)
                
                st.success(f"""
                ### ✅ TRANSACTION CAPTURED SUCCESSFULLY!
                The document and physical signature file have been locked into your workspace layout.
                *   **Document Link Reference:** `{cleaned_ref}`
                *   **Voucher Status:** {has_file_label}
                """)

    st.markdown("---")
    st.subheader("📋 Central Operations Ledger Log (Live Entries)")
    st.dataframe(st.session_state.transfer_ledger, use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: REGISTRIES
# ==========================================
with tab3:
    st.header("⚙️ Core Database Control Panel")
    reg_col1, reg_col2 = st.columns(2)
    with reg_col1:
        st.subheader("➕ Add Sites/Yards")
        new_site = st.text_input("Create New Site / Yard Name:", key="new_site_box")
