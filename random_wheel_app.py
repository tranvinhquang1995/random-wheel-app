import streamlit as st
import random
import time

# Cấu hình giao diện rộng rãi (Wide layout) và tiêu đề trang
st.set_page_config(page_title="Vòng Quay May Mắn - Multiplayer v5", layout="wide")

# CSS để tùy chỉnh giao diện đẹp mắt và ép buộc màu chữ (Hỗ trợ hoàn hảo Dark Mode)
st.markdown("""
<style>
    /* Kiểu dáng cho các ô từ khóa mặc định trong vòng quay */
    .keyword-card {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        background-color: #f0f2f6;
        color: #1E1E1E !important; /* Ép buộc chữ màu tối */
        transition: all 0.1s ease-in-out;
    }
    /* Kiểu dáng cho ô từ khóa đang được chọn/nhấp nháy khi quay */
    .keyword-card-active {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        border: 2px solid #FF4B4B;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        background-color: #FF4B4B;
        color: white !important; /* Ép buộc chữ màu trắng trên nền đỏ */
        transform: scale(1.08);
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.6);
        transition: all 0.05s ease-in-out;
    }
    /* Hiệu ứng nhấp nháy màu vàng dành cho người xem khác khi vòng quay đang chạy */
    .keyword-card-spinning {
        animation: pulse-spin 0.6s infinite alternate;
    }
    @keyframes pulse-spin {
        from { 
            background-color: #f0f2f6; 
            transform: scale(1); 
            border-color: #e0e0e0; 
            color: #1E1E1E !important;
        }
        to { 
            background-color: #FFD700; 
            transform: scale(1.03); 
            border-color: #FFD700; 
            box-shadow: 0px 4px 10px rgba(255, 215, 0, 0.4);
            color: #1E1E1E !important; /* Ép chữ màu tối trên nền vàng */
        }
    }
    /* Hộp nhập từ khóa bên cột trái */
    .input-box {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    /* Kiểu dáng thẻ lịch sử kết quả */
    .history-card {
        background-color: #f8f9fa;
        border-left: 5px solid #FF4B4B;
        padding: 10px 15px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-weight: bold;
        color: #1E1E1E !important; /* Ép buộc chữ màu tối */
        box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# 1. KHỞI TẠO BỘ NHỚ CHIA SẺ TRÊN SERVER (Multiplayer Shared State)
class SharedAppState:
    def __init__(self):
        self.keywords = ["Apple", "Samsung", "Xiaomi", "Oppo", "Vivo", "Realme"]
        self.history = []
        self.is_spinning = False
        self.current_spin_id = 0
        self.last_spin = None  # Lưu: {"id": spin_id, "winner": winner, "timestamp": time.time()}

@st.cache_resource
def get_shared_state():
    return SharedAppState()

shared = get_shared_state()

# Đảm bảo mỗi phiên duyệt web của cá nhân ghi nhận lượt hiển thị popup riêng biệt
if "seen_spin_id" not in st.session_state:
    st.session_state["seen_spin_id"] = 0

# Hàm sinh HTML lưới ô chứa các từ khóa
def render_grid_html(keywords, active_idx=None, is_global_spinning=False):
    if not keywords:
        return "<div style='text-align: center; color: #888; padding: 20px;'>Chưa có từ khóa nào được nhập. Hãy nhập từ khóa ở bảng bên trái!</div>"
    
    cols_html = ""
    for idx, kw in enumerate(keywords):
        if idx == active_idx:
            cols_html += f'<div class="keyword-card-active">{kw}</div>'
        elif is_global_spinning:
            cols_html += f'<div class="keyword-card keyword-card-spinning">{kw}</div>'
        else:
            cols_html += f'<div class="keyword-card">{kw}</div>'
    
    return f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 10px;
        padding: 10px 0;
    ">
        {cols_html}
    </div>
    """

# Giao diện chính của ứng dụng
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🎰 VÒNG QUAY MAY MẮN MULTIPLAYER v5 🎰</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; margin-bottom: 30px;'>Đồng bộ hóa hoàn hảo: Nhập không trùng lặp, khóa khi quay, hiển thị Dark Mode chuẩn!</p>", unsafe_allow_html=True)

# Chia cột chính (Cột trái nhập liệu, Cột phải hiển thị vòng quay)
col_left, col_right = st.columns([1, 2])

# CỘT TRÁI: NHẬP TỪ KHÓA
with col_left:
    st.markdown("<div class='input-box'>", unsafe_allow_html=True)
    st.subheader("📝 Thêm Từ Khóa")
    
    # Khóa ô nhập liệu khi vòng quay đang hoạt động
    if shared.is_spinning:
        st.warning("⚠️ Vòng quay đang hoạt động! Chức năng thêm từ khóa tạm thời bị khóa.")
        st.text_input("Nhập từ khóa mới:", placeholder="Đang khóa...", disabled=True, key="add_kw_input_disabled")
    else:
        st.write("Nhập từ khóa mới rồi ấn nút Thêm hoặc phím Enter:")
        with st.form("add_kw_form", clear_on_submit=True):
            new_kw = st.text_input("Nhập từ khóa mới:", placeholder="Ví dụ: Huawei, Nokia...", key="add_kw_input")
            submit_btn = st.form_submit_button("➕ Thêm vào danh sách", use_container_width=True)
            if submit_btn and new_kw.strip():
                val = new_kw.strip()
                if val not in shared.keywords:
                    shared.keywords.append(val)
                    st.toast(f"Đã thêm từ khóa: {val}")
                    st.rerun()
                else:
                    st.warning("Từ khóa này đã tồn tại trong danh sách!")
                    
    st.markdown("</div>", unsafe_allow_html=True)

# CỘT PHẢI: HIỂN THỊ DANH SÁCH LIVESYNC, VÒNG QUAY & LỊCH SỬ (Tự động cập nhật)
with col_right:
    @st.fragment(run_every=1.5)
    def render_live_area():
        # Kiểm tra lượt quay mới để hiển thị popup đồng bộ
        if shared.last_spin:
            last_id = shared.last_spin["id"]
            last_timestamp = shared.last_spin["timestamp"]
            if last_id != st.session_state["seen_spin_id"] and (time.time() - last_timestamp < 15.0):
                st.session_state["show_winner"] = shared.last_spin["winner"]
                st.session_state["seen_spin_id"] = last_id
                st.rerun()

        col_kw_list, col_wheel, col_hist = st.columns([1, 1.8, 0.9])
        
        # 1. Danh sách từ khóa hiện tại (Có nút xóa)
        with col_kw_list:
            st.markdown("### 📋 Từ Khóa")
            if not shared.keywords:
                st.info("Danh sách trống.")
            else:
                for idx, kw in enumerate(shared.keywords):
                    col_item_text, col_item_btn = st.columns([4, 1.2])
                    # SỬA LỖI MÀU CHỮ: Thêm thuộc tính color: #1e1e1e !important vào inline CSS để không bị trắng chữ ở Dark Mode
                    col_item_text.markdown(
                        f"<div style='padding: 6px; background: #f0f2f6; border-radius: 5px; font-weight: bold; font-size:14px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; color: #1E1E1E !important;'>{kw}</div>", 
                        unsafe_allow_html=True
                    )
                    # Nút xóa nhanh từ khóa (Khóa lại khi đang quay)
                    if col_item_btn.button("❌", key=f"del_{idx}_{kw}", disabled=shared.is_spinning):
                        shared.keywords.pop(idx)
                        st.rerun()
                
                st.write("")
                # Nút dọn dẹp sạch danh sách (Khóa lại khi đang quay)
                if st.button("🗑️ Xóa tất cả", use_container_width=True, key="clear_all", disabled=shared.is_spinning):
                    shared.keywords = []
                    st.rerun()
                    
        # 2. Khung lịch sử góc trên bên phải
        with col_hist:
            st.markdown("<h3 style='margin-top:0;'>🕒 Lịch Sử</h3>", unsafe_allow_html=True)
            if shared.history:
                for idx, winner_item in enumerate(shared.history[:5]):
                    st.markdown(f"<div class='history-card'>#{idx+1}: {winner_item}</div>", unsafe_allow_html=True)
            else:
                st.info("Chưa có lượt quay.")
                
        # 3. Khu vực Vòng Quay chính giữa
        with col_wheel:
            st.markdown("<h3 style='margin-top:0;'>🎯 Trạng Thái Vòng Quay</h3>", unsafe_allow_html=True)
            grid_placeholder = st.empty()
            
            if shared.is_spinning:
                grid_placeholder.markdown(render_grid_html(shared.keywords, is_global_spinning=True), unsafe_allow_html=True)
                st.warning("🎰 Đang có người quay thưởng! Hãy hồi hộp theo dõi...")
                st.button("🚀 ĐANG QUAY...", use_container_width=True, disabled=True, key="spin_disabled_btn")
            else:
                grid_placeholder.markdown(render_grid_html(shared.keywords), unsafe_allow_html=True)
                spin_btn = st.button("🚀 BẮT ĐẦU QUAY NGẪU NHIÊN", use_container_width=True, key="active_spin_btn")
                
                if spin_btn:
                    if len(shared.keywords) < 2:
                        st.error("❌ Vui lòng có ít nhất 2 từ khóa để quay thưởng!")
                    else:
                        shared.is_spinning = True
                        new_spin_id = random.randint(100000, 999999)
                        shared.current_spin_id = new_spin_id
                        
                        start_time = time.time()
                        duration = 10.0
                        num_kws = len(shared.keywords)
                        current_idx = 0
                        
                        while True:
                            elapsed = time.time() - start_time
                            if elapsed >= duration:
                                break
                            
                            progress = elapsed / duration
                            sleep_time = 0.05 + 0.75 * (progress ** 2.5)
                            
                            current_idx = (current_idx + 1) % num_kws
                            grid_placeholder.markdown(render_grid_html(shared.keywords, active_idx=current_idx), unsafe_allow_html=True)
                            time.sleep(sleep_time)
                        
                        winner_idx = random.randint(0, num_kws - 1)
                        winner_name = shared.keywords[winner_idx]
                        
                        grid_placeholder.markdown(render_grid_html(shared.keywords, active_idx=winner_idx), unsafe_allow_html=True)
                        
                        shared.history.insert(0, winner_name)
                        shared.last_spin = {
                            "id": new_spin_id,
                            "winner": winner_name,
                            "timestamp": time.time()
                        }
                        shared.is_spinning = False
                        
                        st.session_state["show_winner"] = winner_name
                        st.session_state["seen_spin_id"] = new_spin_id
                        st.rerun()

    render_live_area()

# 3. HIỂN THỊ POPUP THÔNG BÁO CHIẾN THẮNG (Tự động tắt sau 3 giây)
if "show_winner" in st.session_state:
    winner = st.session_state["show_winner"]
    st.balloons()
    
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 30%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: white;
        padding: 30px 40px;
        border-radius: 16px;
        box-shadow: 0px 12px 40px rgba(0,0,0,0.3);
        z-index: 10000;
        text-align: center;
        border: 4px solid #FF4B4B;
        width: 480px;
    ">
        <h2 style="color: #FF4B4B; margin-top: 0; font-size: 32px; letter-spacing: 1px;">🎉 CHÚC MỪNG! 🎉</h2>
        <p style="font-size: 18px; color: #555; margin-bottom: 5px;">Kết quả may mắn nhận được là:</p>
        <p style="font-size: 36px; font-weight: bold; color: #1E1E1E !important; margin: 15px 0; border-bottom: 2px dashed #f0f2f6; padding-bottom: 15px;">{winner}</p>
        <div style="
            width: 100%;
            background-color: #f0f2f6;
            border-radius: 10px;
            height: 6px;
            margin-top: 20px;
            overflow: hidden;
        ">
            <div style="
                background-color: #FF4B4B;
                height: 100%;
                width: 100%;
                animation: countdown-bar 3s linear forwards;
            "></div>
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 8px;">Thông báo này sẽ tự động đóng sau 3 giây...</p>
    </div>
    <style>
        @keyframes countdown-bar {{
            from {{ width: 100%; }}
            to {{ width: 0%; }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    time.sleep(3)
    del st.session_state["show_winner"]
    st.rerun()
