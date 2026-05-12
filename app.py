import streamlit as st  
import os  
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd   
import numpy as np  
from joblib import Parallel, delayed  
import glob  
import time  
from streamlit_javascript import st_javascript
from dataprocessing1 import( 
    extract_and_clean_zip_files, 
    get_files_by_group, clean_data, 
    read_excel_files_from_list, 
    summarize_variance_by_month,
    get_latest_budget_folder
)
from plot4group import plot_summary_stacked_PC, plot_summary_stacked_TV
from ALL.ALLDATA import process_all_data_with_plotly_PC, process_all_data_with_plotly_TV
import zipfile
import re  
from datetime import datetime
import warnings  
from streamlit.components.v1 import html



def rerun_processing():
    extract_and_clean_zip_files(r"Data_Link")
rerun_processing()


warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)  
  
st.set_page_config(page_title="Cost DX", page_icon="purchase.svg", layout="wide", initial_sidebar_state="collapsed")  
with open("style.css") as f:  
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)  


def get_folder_timestamp(folder_path):  
    file_list = glob.glob(os.path.join(folder_path, '*.xlsx'))  
    if not file_list:  
        return 0  
    return max([os.path.getmtime(f) for f in file_list])  

def main_PC():  
    budget_folder = get_latest_budget_folder()
    current_fy = "Tự động" if budget_folder else "Không tìm thấy"
    
    st.title('Cost DX')

    # col1, col2 = st.columns([3, 1])
    # with col1:
    #     st.title('Cost DX')
    # with col2:
    #     st.info(f"📅 FY: **{current_fy}** | Auto-detect")
    
    folders = ['All', 'Assy', 'Control', 'Diecast', 'Process', 'DETAILS OF TOTAL COST']
    selected_folders = st.multiselect(
        "Select groups to compare (max 4):",
        folders, 
        default=['All'], 
        max_selections=4,
        key='folder_selector'
    )
    base_path = budget_folder

  
    if not selected_folders:  
        st.warning('Please select at least 1 group to compare!')  
        st.stop()  
    
    # Kiểm tra nếu người dùng chọn "DETAILS OF TOTAL COST"
    if 'DETAILS OF TOTAL COST' in selected_folders:
        st.link_button(
            "Open Details of Total Cost", 
            "http://10.122.72.1:8508/",
            type="primary"
        )
        
        # Loại bỏ 'DETAILS OF TOTAL COST' khỏi danh sách
        selected_folders = [f for f in selected_folders if f != 'DETAILS OF TOTAL COST']
        
        # Nếu không còn folder nào sau khi loại bỏ DETAILS, dừng
        if not selected_folders:
            st.warning('Please select at least 1 group to compare!')
            st.stop()

  
    def show_folder_chart(folder):
        if folder == 'All':
            fig = process_all_data_with_plotly_PC()
        else:
            # TỰ ĐỘNG lấy thư mục FY mới nhất
            #budget_folder = get_latest_budget_folder()
            folder_path = base_path
            
            files = get_files_by_group(folder_path, folder)
            if not files:
                st.warning(f"No data for {folder} trong FY hiện tại")
                return
            
            folder_ts = get_folder_timestamp(folder_path)
            try:
                df = read_excel_files_from_list(files, folder_ts)
            except Exception as e:
                st.warning(f"Error reading group {folder}: {e}")
                return
            
            if df is None or df.empty:
                st.warning(f"No data for group {folder}")
                return
            
            summary_df = summarize_variance_by_month(df)
            fig = plot_summary_stacked_PC(summary_df, folder)

        st.plotly_chart(fig, use_container_width=True)
  
    num = len(selected_folders)  
    if num == 4:  
        rows = [st.columns(2), st.columns(2)]  
        for idx, folder in enumerate(selected_folders):  
            row = rows[idx // 2]  
            with row[idx % 2]:  
                show_folder_chart(folder)  
    elif num == 3:  
        row1 = st.columns(2)  
        row2 = st.columns(1)  
        for i in range(2):  
            with row1[i]:  
                show_folder_chart(selected_folders[i])  
        with row2[0]:  
            show_folder_chart(selected_folders[2])  
    else:  
        cols = st.columns(num)  
        for i, folder in enumerate(selected_folders):  
            with cols[i]:  
                show_folder_chart(folder)

def main_TV():  
    slide_folders = ['All', 'Assy', 'Control', 'Diecast', 'Process']  
    slide_titles = {  
        'All': "Cost for All",  
        'Assy': "Cost for Assy",  
        'Control': "Cost for Control",  
        'Diecast': "Cost for Diecast",  
        'Process': "Cost for Process"  
    }  
    SLIDE_TIME = 10
    
  
    # Khởi tạo session_state cho slide_idx và paused  
    if 'slide_idx' not in st.session_state:  
        st.session_state.slide_idx = 0  
    if 'paused' not in st.session_state:  
        st.session_state.paused = False  
        
    # SLIDE - TỰ ĐỘNG FY
    budget_folder = get_latest_budget_folder()
    current_folder = slide_folders[st.session_state.slide_idx]  
    folder_ts = 0  
    
    if budget_folder:
        base_path = budget_folder  # FY tự động (FY25)pip
        folder_path = base_path    # Dùng trực tiếp FY folder
    
    if os.path.exists(folder_path):
        try:
            file_list = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
            if file_list:
                folder_ts = max([os.path.getmtime(os.path.join(folder_path, f)) for f in file_list])
            else:
                print(f"Slide {current_folder}: Không có file .xlsx")
        except Exception as e:
            print(f"Lỗi đọc slide folder: {e}")
            folder_ts = 0
    else:
        print("Không có thư mục BUDGET FY nào")

  
     
    st.title('Bảng theo dõi chi phí tháng/月々の経費フォロー表')
    st.markdown(f"<h3 class='centered'>{slide_titles[current_folder]}</h3>", unsafe_allow_html=True)
  
    if current_folder == 'All':  
        # Hàm xử lý cho nhóm All
        fig = process_all_data_with_plotly_TV()  
    else:  
        files = get_files_by_group(base_path, current_folder)  
        if not files:  
            st.warning(f"No data for {current_folder}")  
            return  
        folder_ts = get_folder_timestamp(base_path)  
        aggregated_data = read_excel_files_from_list(files, folder_ts)  
        if aggregated_data is None or aggregated_data.empty or "Month" not in aggregated_data.columns:  
            st.warning(f"No usable data for {current_folder}")  
            return  
        summary_df = summarize_variance_by_month(aggregated_data)  
        fig = plot_summary_stacked_TV(summary_df, current_folder)  
    st.plotly_chart(fig, use_container_width=True)  
        # st.caption(f"Slide {st.session_state.slide_idx+1}/{len(slide_folders)}: {current_folder}")  
  
    # Nút Pause/Resume và xử lý trạng thái  
    col1, col2, col3 = st.columns([0.95,1,30])  
    with col1:  
        prev_clicked = st.button('⏮', key='previous')  
    with col2:  
        pause_clicked = st.button(  
            '⏸' if not st.session_state.paused else '▶', key='pause')  
    with col3:  
        next_clicked = st.button('⏭', key='next')     
  
    if prev_clicked:  
        st.session_state.slide_idx = (st.session_state.slide_idx - 1) % len(slide_folders)  
        st.rerun()  
    elif next_clicked:  
        st.session_state.slide_idx = (st.session_state.slide_idx + 1) % len(slide_folders)  
        st.rerun()  
    elif pause_clicked:  
        st.session_state.paused = not st.session_state.paused  
        st.rerun() 
    
    # Khi không pause thì trở slide tiếp theo sau mỗi SLIDE_TIME giây  
    if not st.session_state.paused:  
        time.sleep(SLIDE_TIME)  
        st.session_state.slide_idx = (st.session_state.slide_idx + 1) % len(slide_folders)  
        st.rerun()


def is_tv_device(user_agent):  
    """Detect if the user agent belongs to a SMART TV/Android TV device."""  
    if not isinstance(user_agent, str) or not user_agent:  
        return False  
    tv_patterns = [  
        r"Android.*TV", r"SmartTV", r"SMART\-TV", r"GoogleTV", r"AppleTV", r"HbbTV", r"WebTV",  
        r"NetCast", r"Viera", r"SmartHub", r"BRAVIA", r"Opera TV",  
        r"(Samsung|LG|Sony|Panasonic|Philips|Toshiba|Sharp).*TV",  
        r"Tizen", r"SamsungBrowser",  
        r"\bTV\b"  
    ] 
    for pat in tv_patterns:  
        if re.search(pat, user_agent, re.IGNORECASE):  
            return True  
    return False  


def mode_selector():  
    if "mode" not in st.session_state:  
        user_agent = st_javascript("navigator.userAgent")  
        # Chỉ khi nào user_agent trả về kết quả hợp lệ thì mới set mode  
        if user_agent and "Mozilla" in user_agent:  
            if is_tv_device(user_agent):  
                st.session_state.mode = "tv"  
            else:  
                st.session_state.mode = "pc"  
            st.rerun()    # Bắt buộc rerun để cập nhật giao diện đúng với mode  
        else:  
            # Hiển thị info đang đợi user_agent  
            st.info("Đang xác định thiết bị, vui lòng chờ...")  
            st.stop()  
    # Nút chuyển mode thủ công  
    with st.sidebar:  
        st.sidebar.title('')
        if st.session_state.mode == "pc":  
            label = "Slide Mode"  
            help_text = "Chế độ trình chiếu"  
        else:  
            label = "Website Mode"  
            help_text = "Chế độ website"  
        if st.button(label, help=help_text):  
            st.session_state.mode = "tv" if st.session_state.mode == "pc" else "pc"  
            st.rerun()   


# =====================================================================
# MAIN APP
# =====================================================================

mode_selector()

# THÊM SIDEBAR CHI TIẾT COST DX
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Chi tiết COST DX")
    
    if st.button("📦 CHI PHÍ XUẤT KHO TỔNG", use_container_width=True):
        st.session_state.page = "xuatkho"
        st.rerun()
    
    # Nếu đang ở page xuatkho, hiển thị nút quay lại
    if st.session_state.get('page') == 'xuatkho':
        if st.button("⬅️ Quay lại trang chính", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()


# Kiểm tra page và hiển thị nội dung tương ứng
if st.session_state.get('page') == 'xuatkho':
    # Import và chạy hàm từ data_processing
    try:
        from Nam.Chiphitong import main_xuatkho
        main_xuatkho()
    except ImportError:
        st.error("Không tìm thấy file data_processing.py hoặc hàm main_xuatkho()")
        st.info("Vui lòng tạo hàm main_xuatkho() trong file data_processing.py")
else:
    # Code gốc - hiển thị trang chính
    if st.session_state.get('mode', 'pc') == 'pc':  
        main_PC()  
    else:  
        main_TV()





