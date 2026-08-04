import streamlit as st
import random
import time

# Cấu hình giao diện rộng rãi (Wide layout) và tiêu đề trang
st.set_page_config(page_title="Vòng Quay May Mắn - Multiplayer v10", layout="wide")

# CSS ĐẶC BIỆT: Khóa cứng Dark Mode, ẩn menu cài đặt, nút 3 chấm và footer của Streamlit
st.markdown("""
<style>
    /* 1. ẨN HOÀN TOÀN MENU BA CHẤM (SETTINGS) VÀ FOOTER ĐỂ NGƯỜI DÙNG KHÔNG THỂ CHUYỂN CHẾ ĐỘ */
    #MainMenu {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    div[data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    
    /* 2. ÉP BUỘC TOÀN BỘ NỀN TRANG CHÍNH VÀ CHỮ SANG TÔNG TỐI (DARK MODE) */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }
    
    /* Đồng bộ màu chữ cho các tiêu đề lớn */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #ffffff !important;
    }

    /* 3. THIẾT KẾ CÁC Ô TỪ KHÓA MẶC ĐỊNH (Tông tối gaming) */
    .keyword-card {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        border: 2px solid #3c4048;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        background-color: #1e222b !important;
        color: #ffffff !important;
        transition: all 0.1s ease-in-out;
    }
    /* Kiểu dáng cho ô từ khóa đang được chọn/nhấp nháy khi quay (Đỏ Neon rực rỡ) */
    .keyword-card-active {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        border: 2px solid #FF4B4B;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        background-color: #FF4B4B !important;
        color: #ffffff !important;
        transform: scale(1.08);
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.8);
        transition: all 0.05s ease-in-out;
    }
    /* Hiệu ứng nhấp nháy màu vàng dành cho người xem khác khi vòng quay đang chạy */
    .keyword-card-spinning {
        animation: pulse-spin 0.6s infinite alternate;
    }
    @keyframes pulse-spin {
        from { background-color: #1e222b !important; transform: scale(1); border-color: #3c4048; }
        to { background-color: #FFD700 !important; transform: scale(1.03); border-color: #FFD700; box-shadow: 0px 4px 10px rgba(255, 215, 0, 0.6); }
    }
    
    /* 4. HỘP NHẬP TỪ KHÓA BÊN CỘT TRÁI (Tông xám tối) */
    .input-box {
        background-color: #1e222b !important;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #3c4048 !important;
    }
    
    /* 5. KIỂU DÁNG THẺ LỊCH SỬ KẾ QUẢ (Đồng bộ Dark Mode) */
    .history-card {
        background-color: #1e222b !important;
        border-left: 5px solid #FF4B4B;
        padding: 10px 15px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-weight: bold;
        color: #ffffff !important;
        border-top: 1px solid #3c4048;
        border-right: 1px solid #3c4048;
        border-bottom: 1px solid #3c4048;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.2);
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
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🎰 VÒNG QUAY MAY MẮN MULTIPLAYER v10 🎰</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; margin-bottom: 30px; color: #cccccc !important;'>Đã khóa cứng giao diện Dark Mode & dọn dẹp hoàn toàn viền hộp thừa!</p>", unsafe_allow_html=True)

# Chia cột chính
col_left, col_right = st.columns([1, 2])

# CỘT TRÁI: NHẬP TỪ KHÓA
with col_left:
    st.markdown("<div class='input-box'>", unsafe_allow_html=True)
    st.subheader("📝 Thêm Từ Khóa")
    
    # Kiểm tra trạng thái quay toàn cục để khóa ô nhập
    is_locked = shared.is_spinning
    
    if is_locked:
        st.warning("⚠️ Vòng quay đang hoạt động! Chức năng thêm từ khóa tạm thời bị khóa.")
    else:
        st.write("Nhập từ khóa mới rồi ấn Enter hoặc nút Thêm:")

    # Hàm callback xử lý thêm từ khóa không cần st.form
    def handle_add():
        if "add_kw_input" in st.session_state:
            val = st.session_state["add_kw_input"].strip()
            if val:
                if val not in shared.keywords:
                    shared.keywords.append(val)
                    st.toast(f"Đã thêm từ khóa: {val}")
                else:
                    st.warning("Từ khóa này đã tồn tại trong danh sách!")
                # Xóa sạch text trong ô sau khi xử lý thành công
                st.session_state["add_kw_input"] = ""

    # Ô nhập liệu phẳng (Sử dụng callback trực tiếp, KHÔNG dùng st.form để triệt tiêu hoàn toàn viền xám thừa)
    st.text_input(
        "Nhập từ khóa mới:", 
        placeholder="Gõ từ khóa tại đây...", 
        key="add_kw_input",
        disabled=is_locked,
        label_visibility="collapsed",
        on_change=handle_add
    )
    
    # Nút thêm thủ công (gọi callback trực tiếp)
    if st.button("➕ Thêm vào danh sách", use_container_width=True, disabled=is_locked, key="add_btn_manual"):
        handle_add()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# CỘT PHẢI: HIỂN THỊ DANH SÁCH LIVESYNC, VÒNG QUAY & LÌCH SỬ (Tự động cập nhật qua Fragment)
with col_right:
    @st.fragment(run_every=1.5)
    def render_live_area():
        # Kiểm tra xem có kết quả quay mới từ người dùng khác không để kích hoạt popup đồng bộ
        if shared.last_spin:
            last_id = shared.last_spin["id"]
            last_timestamp = shared.last_spin["timestamp"]
            # Chỉ hiển thị popup nếu đó là lượt quay mới và diễn ra trong vòng 15 giây qua
            if last_id != st.session_state["seen_spin_id"] and (time.time() - last_timestamp < 15.0):
                st.session_state["show_winner"] = shared.last_spin["winner"]
                st.session_state["seen_spin_id"] = last_id
                st.rerun()

        # Chia cột nhỏ bên trong vùng fragment
        col_kw_list, col_wheel, col_hist = st.columns([1, 1.8, 0.9])
        is_locked = shared.is_spinning
        
        # 1. Danh sách từ khóa trực quan (Cập nhật trực tiếp khi người khác thêm/xóa)
        with col_kw_list:
            st.markdown("### 📋 Từ Khóa Hiện Tại")
            if not shared.keywords:
                st.info("Danh sách trống. Vui lòng thêm từ khóa!")
            else:
                for idx, kw in enumerate(shared.keywords):
                    col_item_text, col_item_btn = st.columns([4, 1])
                    # Hiển thị từ khóa dạng khối bo góc tông tối cực ngầu
                    col_item_text.markdown(f"<div style='padding: 6px; background: #1e222b; border: 1px solid #3c4048; border-radius: 5px; font-weight: bold; font-size:14px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; color: #ffffff !important;'>{kw}</div>", unsafe_allow_html=True)
                    # Nút xóa nhanh từ khóa đó (Bị khóa khi đang quay)
                    if col_item_btn.button("❌", key=f"del_{idx}_{kw}", disabled=is_locked):
                        shared.keywords.pop(idx)
                        st.rerun()
                
                st.write("")
                # Nút dọn dẹp sạch danh sách (Bị khóa khi đang quay)
                if st.button("🗑️ Xóa tất cả", use_container_width=True, key="clear_all", disabled=is_locked):
                    shared.keywords = []
                    st.rerun()
                    
        # 2. Khung lịch sử góc trên bên phải
        with col_hist:
            st.markdown("<h3 style='margin-top:0;'>🕒 Lịch Sử</h3>", unsafe_allow_html=True)
            if shared.history:
                for idx, winner_item in enumerate(shared.history[:5]):
                    st.markdown(f"<div class='history-card'>#{idx+1}: {winner_item}</div>", unsafe_allow_html=True)
            else:
                st.info("Chưa có lượt quay nào.")
                
        # 3. Khu vực Vòng Quay May Mắn chính giữa
        with col_wheel:
            st.markdown("<h3 style='margin-top:0;'>🎯 Trạng Thái Vòng Quay</h3>", unsafe_allow_html=True)
            grid_placeholder = st.empty()
            
            # Giao diện vòng quay theo trạng thái
            if shared.is_spinning:
                # Những người dùng khác đang xem sẽ thấy các ô chuyển động nhấp nháy màu vàng
                grid_placeholder.markdown(render_grid_html(shared.keywords, is_global_spinning=True), unsafe_allow_html=True)
                st.warning("🎰 Đang có người quay thưởng! Hãy hồi hộp theo dõi...")
                st.button("🚀 ĐANG QUAY...", use_container_width=True, disabled=True, key="spin_disabled_btn")
            else:
                # Trạng thái tĩnh bình thường
                grid_placeholder.markdown(render_grid_html(shared.keywords), unsafe_allow_html=True)
                spin_btn = st.button("🚀 BẮT ĐẦU QUAY NGẪU NHIÊN", use_container_width=True, key="active_spin_btn")
                
                if spin_btn:
                    if len(shared.keywords) < 2:
                        st.error("❌ Vui lòng có ít nhất 2 từ khóa để quay thưởng!")
                    else:
                        # Bắt đầu quy trình quay
                        shared.is_spinning = True
                        new_spin_id = random.randint(100000, 999999)
                        shared.current_spin_id = new_spin_id
                        
                        # Hiệu ứng chạy vòng tròn giảm tốc cơ học trong ~10 giây
                        start_time = time.time()
                        duration = 10.0
                        num_kws = len(shared.keywords)
                        current_idx = 0
                        
                        while True:
                            elapsed = time.time() - start_time
                            if elapsed >= duration:
                                break
                            
                            # Công thức giảm tốc tăng thời gian trễ theo đồ thị hàm mũ
                            progress = elapsed / duration
                            sleep_time = 0.05 + 0.75 * (progress ** 2.5)
                            
                            current_idx = (current_idx + 1) % num_kws
                            grid_placeholder.markdown(render_grid_html(shared.keywords, active_idx=current_idx), unsafe_allow_html=True)
                            time.sleep(sleep_time)
                        
                        # Xác định kết quả chiến thắng cuối cùng
                        winner_idx = random.randint(0, num_kws - 1)
                        winner_name = shared.keywords[winner_idx]
                        
                        # Làm sáng rực ô chiến thắng
                        grid_placeholder.markdown(render_grid_html(shared.keywords, active_idx=winner_idx), unsafe_allow_html=True)
                        
                        # Đồng bộ hóa kết quả lên bộ nhớ chung
                        shared.history.insert(0, winner_name)
                        shared.last_spin = {
                            "id": new_spin_id,
                            "winner": winner_name,
                            "timestamp": time.time()
                        }
                        shared.is_spinning = False
                        
                        # Kích hoạt hiển thị popup cục bộ
                        st.session_state["show_winner"] = winner_name
                        st.session_state["seen_spin_id"] = new_spin_id
                        st.rerun()

    render_live_area()

# 3. HIỂN THỊ POPUP THÔNG BÁO CHIẾN THẮNG (Tự động tắt sau 3 giây)
if "show_winner" in st.session_state:
    winner = st.session_state["show_winner"]
    st.balloons()  # Hiệu ứng bong bóng bay chúc mừng toàn màn hình
    
    # Hộp thông báo Modal Overlay đè lên giao diện chính màu tối cực ngầu
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 30%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: #1a1c23;
        padding: 30px 40px;
        border-radius: 16px;
        box-shadow: 0px 12px 40px rgba(0,0,0,0.6);
        z-index: 10000;
        text-align: center;
        border: 4px solid #FF4B4B;
        width: 480px;
    ">
        <h2 style="color: #FF4B4B !important; margin-top: 0; font-size: 32px; letter-spacing: 1px;">🎉 CHÚC MỪNG! 🎉</h2>
        <p style="font-size: 18px; color: #cccccc !important; margin-bottom: 5px;">Kết quả may mắn nhận được là:</p>
        <p style="font-size: 36px; font-weight: bold; color: #FFD700 !important; margin: 15px 0; border-bottom: 2px dashed #3c4048; padding-bottom: 15px;">{winner}</p>
        <div style="
            width: 100%;
            background-color: #2b303c;
            border-radius: 10px;
            height: 6px;
            margin-top: 20px;
            overflow: hidden;
        ">
            <!-- Thanh thời gian 3 giây co ngắn dần bằng CSS Animation -->
            <div style="
                background-color: #FF4B4B;
                height: 100%;
                width: 100%;
                animation: countdown-bar 3s linear forwards;
            "></div>
        </div>
        <p style="font-size: 12px; color: #888888 !important; margin-top: 8px;">Thông báo này sẽ tự động đóng sau 3 giây...</p>
    </div>
    <style>
        @keyframes countdown-bar {{
            from {{ width: 100%; }}
            to {{ width: 0%; }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Dừng 3 giây rồi xóa trạng thái để ẩn popup và làm mới trang
    time.sleep(3)
    del st.session_state["show_winner"]
    st.rerun()

# 4. KHUNG FOOTER COPYRIGHT CHUYÊN NGHIỆP
st.markdown("""
<div style="
    text-align: center;
    margin-top: 80px;
    padding: 20px;
    border-top: 1px solid #3c4048;
    color: #888888 !important;
    font-size: 14px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: transparent;
">
    © 2026 - Developed by Nobita | Vòng Quay May Mắn Multiplayer
</div>
""", unsafe_allow_html=True)
