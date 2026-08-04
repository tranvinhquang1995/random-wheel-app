import streamlit as st
import random
import time

# Cấu hình giao diện rộng rãi (Wide layout) và tiêu đề trang
st.set_page_config(page_title="Vòng Quay May Mắn - Multiplayer Random Wheel", layout="wide")

# CSS để tùy chỉnh giao diện đẹp mắt
st.markdown("""
<style>
    /* Kiểu dáng cho các ô từ khóa mặc định */
    .keyword-card {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        background-color: #f0f2f6;
        color: #31333F;
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
        color: white;
        transform: scale(1.08);
        box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.6);
        transition: all 0.05s ease-in-out;
    }
    /* Hiệu ứng nhấp nháy màu vàng dành cho người xem khác khi vòng quay đang chạy */
    .keyword-card-spinning {
        animation: pulse-spin 0.6s infinite alternate;
    }
    @keyframes pulse-spin {
        from { background-color: #f0f2f6; transform: scale(1); border-color: #e0e0e0; }
        to { background-color: #FFD700; transform: scale(1.03); border-color: #FFD700; box-shadow: 0px 4px 10px rgba(255, 215, 0, 0.4); }
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
        self.num_inputs = 10

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
        return "<div style='text-align: center; color: #888; padding: 20px;'>Chưa có từ khóa nào được nhập.</div>"
    
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
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🎰 VÒNG QUAY MAY MẮN MULTIPLAYER 🎰</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; margin-bottom: 30px;'>Mọi người truy cập cùng một link đều có thể thêm từ khóa và xem kết quả quay trực tiếp theo thời gian thực!</p>", unsafe_allow_html=True)

# Chia cột
col_left, col_right = st.columns([1, 2])

# CỘT TRÁI: NHẬP TỪ KHÓA
with col_left:
    st.markdown("<div class='input-box'>", unsafe_allow_html=True)
    st.subheader("📝 Danh Sách Từ Khóa")
    st.write("Nhập từ khóa vào các ô bên dưới:")
    
    temp_keywords = []
    
    # Tạo các ô nhập từ khóa động dựa trên số lượng được thiết lập
    for i in range(shared.num_inputs):
        default_val = shared.keywords[i] if i < len(shared.keywords) else ""
        user_input = st.text_input(f"Ô nhập #{i+1}", value=default_val, key=f"input_kw_{i}")
        if user_input.strip():
            temp_keywords.append(user_input.strip())
            
    # Cập nhật danh sách chung khi có bất kì ô nào thay đổi
    if temp_keywords != shared.keywords:
        shared.keywords = temp_keywords
        
    st.write(f"👉 Số từ khóa hợp lệ: **{len(shared.keywords)}**")
    
    # Nút bấm tăng thêm ô nhập hoặc xóa nhanh
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Thêm 5 ô nhập", use_container_width=True):
            shared.num_inputs += 5
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Xóa tất cả", use_container_width=True):
            shared.keywords = []
            for i in range(shared.num_inputs):
                if f"input_kw_{i}" in st.session_state:
                    st.session_state[f"input_kw_{i}"] = ""
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

# CỘT PHẢI: HIỂN THỊ VÒNG QUAY & LỊCH SỬ (Được cập nhật tự động bằng Fragment)
with col_right:
    @st.fragment(run_every=1.5)
    def render_right_side():
        col_main, col_hist = st.columns([2.5, 1])
        
        # Kiểm tra xem có kết quả quay mới từ người dùng khác không để kích hoạt popup đồng bộ
        if shared.last_spin:
            last_id = shared.last_spin["id"]
            last_timestamp = shared.last_spin["timestamp"]
            # Chỉ hiển thị popup nếu đó là lượt quay mới và diễn ra trong vòng 15 giây qua
            if last_id != st.session_state["seen_spin_id"] and (time.time() - last_timestamp < 15.0):
                st.session_state["show_winner"] = shared.last_spin["winner"]
                st.session_state["seen_spin_id"] = last_id
                st.rerun()

        # Hiển thị lịch sử góc trên bên phải
        with col_hist:
            st.markdown("<h3 style='margin-top:0;'>🕒 Lịch Sử</h3>", unsafe_allow_html=True)
            st.write("5 lượt quay gần nhất:")
            if shared.history:
                for idx, winner_item in enumerate(shared.history[:5]):
                    st.markdown(f"<div class='history-card'>#{idx+1}: {winner_item}</div>", unsafe_allow_html=True)
            else:
                st.info("Chưa có lượt quay.")

        # Hiển thị vòng quay chữ nhật chính giữa bên phải
        with col_main:
            st.markdown("<h3 style='margin-top:0;'>🎯 Trạng Thái Vòng Quay</h3>", unsafe_allow_html=True)
            grid_placeholder = st.empty()
            
            # Cấu hình hiển thị theo trạng thái quay
            if shared.is_spinning:
                # Những người dùng khác đang xem sẽ thấy các ô chuyển động nhấp nháy màu vàng
                grid_placeholder.markdown(render_grid_html(shared.keywords, is_global_spinning=True), unsafe_allow_html=True)
                st.warning("🎰 Đang có người quay thưởng! Hãy hồi hộp theo dõi...")
                st.button("🚀 ĐANG QUAY...", use_container_width=True, disabled=True)
            else:
                # Trạng thái tĩnh bình thường
                grid_placeholder.markdown(render_grid_html(shared.keywords), unsafe_allow_html=True)
                spin_btn = st.button("🚀 BẮT ĐẦU QUAY NGẪU NHIÊN", use_container_width=True)
                
                if spin_btn:
                    if len(shared.keywords) < 2:
                        st.error("❌ Vui lòng nhập ít nhất 2 từ khóa ở cột bên trái để quay thưởng!")
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

    render_right_side()

# 3. HIỂN THỊ POPUP THÔNG BÁO CHIẾN THẮNG (Tự động tắt sau 3 giây)
if "show_winner" in st.session_state:
    winner = st.session_state["show_winner"]
    st.balloons()  # Hiệu ứng bong bóng bay chúc mừng toàn màn hình
    
    # Hộp thông báo Modal Overlay đè lên giao diện chính
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
        <p style="font-size: 36px; font-weight: bold; color: #1E1E1E; margin: 15px 0; border-bottom: 2px dashed #f0f2f6; padding-bottom: 15px;">{winner}</p>
        <div style="
            width: 100%;
            background-color: #f0f2f6;
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
        <p style="font-size: 12px; color: #999; margin-top: 8px;">Thông báo này sẽ tự động đóng sau 3 giây...</p>
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
