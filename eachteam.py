import os
import zipfile
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import re
from pathlib import Path
import time
import shutil


class UnifiedCostVisualization:
    def __init__(self, base_path):
        self.base_path = base_path
        self.months_data = {}
        self.teams = ['All', 'Control', 'Assy', 'Process', 'Die cast']
        
    def unzip_files(self, folder_path):
        zip_files = [f for f in os.listdir(folder_path) if f.endswith('.zip')]
        
        if zip_files:
            st.info(f"🔍 New zip file detected: {', '.join(zip_files)}")
            
            for zip_file in zip_files:
                zip_path = os.path.join(folder_path, zip_file)
                extract_folder_name = zip_file.replace('.zip', '')
                extract_path = os.path.join(folder_path, extract_folder_name)
                
                if os.path.exists(extract_path):
                    st.warning(f"🗑️ Deleting old folder: {extract_folder_name}")
                    try:
                        shutil.rmtree(extract_path)
                        st.success(f"✅ Old folder deleted")
                    except Exception as e:
                        st.error(f"❌ Cannot delete old folder: {e}")
                        return None
                
                st.info(f"📦 Extracting new file: {zip_file}")
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    st.success(f"✅ Extracted to: {extract_folder_name}")
                    
                    os.remove(zip_path)
                    st.success(f"🗑️ Zip file deleted: {zip_file}")
                    
                    return extract_path
                    
                except Exception as e:
                    st.error(f"❌ Extraction error: {e}")
                    return None
        else:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    if self.find_export_folder(item_path):
                        return item_path
            
            return folder_path
    
    def find_export_folder(self, search_path):
        """Find folder with name starting with 'XUẤT KHO'"""
        try:
            for folder in os.listdir(search_path):
                folder_path = os.path.join(search_path, folder)
                if os.path.isdir(folder_path) and folder.upper().startswith('XUẤT KHO'):
                    return folder_path
        except:
            pass
        return None
    
    def get_month_folders(self, export_path):
        """Get list of month folders"""
        month_folders = {}
        
        for folder in os.listdir(export_path):
            folder_path = os.path.join(export_path, folder)
            if os.path.isdir(folder_path):
                match = re.search(r'Tháng\s+(\d{1,2})\.(\d{4})', folder, re.IGNORECASE)
                if match:
                    month = int(match.group(1))
                    year = int(match.group(2))
                    month_folders[month] = {'path': folder_path, 'year': year}
        
        return month_folders
    
    def classify_team(self, team_str):
        """Classify team from column G"""
        if pd.isna(team_str):
            return None
        
        team_str = str(team_str).strip()
        
        # Control = MA
        if team_str.upper() == 'MA':
            return 'Control'
        # Assy = contains 'Assy'
        elif 'ASSY' in team_str.upper():
            return 'Assy'
        # Process
        elif 'PROCESS' in team_str.upper():
            return 'Process'
        # Die cast
        elif 'DIE' in team_str.upper() and 'CAST' in team_str.upper():
            return 'Die cast'
        else:
            return None
    
    def process_excel_file(self, excel_path):
        """
        Read Excel file from sheet 'HUONG (KO XOA)'
        Column C (index 2) = Category
        Column D (index 3) = Amount
        Column G (index 6) = Team
        """
        try:
            sheet_name = 'HUONG (KO XOA)'
            
            df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
            
            category_data = df_raw.iloc[1:, 2].dropna()
            amount_data = df_raw.iloc[1:, 3]
            team_data = df_raw.iloc[1:, 6]
            
            df = pd.DataFrame({
                'Category': category_data.values,
                'Amount': amount_data.values[:len(category_data)],
                'Team': team_data.values[:len(category_data)]
            })
            
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df.dropna(subset=['Amount'])
            
            df['Category'] = df['Category'].astype(str).str.strip()
            df['Team_Classified'] = df['Team'].apply(self.classify_team)
            
            # Calculate for All (total)
            result = {}
            
            # All teams combined
            bm_total_all = df[df['Category'].str.upper() == 'BM']['Amount'].sum()
            th_total_all = df[df['Category'].str.contains(
                'Tiêu hao|tiêu hao|TIÊU HẠO', case=False, na=False, regex=True)]['Amount'].sum()
            pm_total_all = df[df['Category'].str.upper() == 'PM']['Amount'].sum()
            cm_total_all = df[df['Category'].str.upper() == 'CM']['Amount'].sum()
            pm_cm_total_all = pm_total_all + cm_total_all
            
            result['All'] = {
                'BM': bm_total_all,
                'TH': th_total_all,
                'PM_CM': pm_cm_total_all
            }
            
            # Calculate for each team
            for team in ['Control', 'Assy', 'Process', 'Die cast']:
                df_team = df[df['Team_Classified'] == team]
                
                if df_team.empty:
                    result[team] = {'BM': 0, 'TH': 0, 'PM_CM': 0}
                    continue
                
                bm_total = df_team[df_team['Category'].str.upper() == 'BM']['Amount'].sum()
                
                th_total = df_team[df_team['Category'].str.contains(
                    'Tiêu hao|tiêu hao|TIÊU HẠO', case=False, na=False, regex=True)]['Amount'].sum()
                
                pm_total = df_team[df_team['Category'].str.upper() == 'PM']['Amount'].sum()
                cm_total = df_team[df_team['Category'].str.upper() == 'CM']['Amount'].sum()
                pm_cm_total = pm_total + cm_total
                
                result[team] = {
                    'BM': bm_total,
                    'TH': th_total,
                    'PM_CM': pm_cm_total
                }
            
            return result
            
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None
    
    def find_excel_in_month_folder(self, month_folder_path):
        """Find Excel file in month folder"""
        for file in os.listdir(month_folder_path):
            if file.endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                return os.path.join(month_folder_path, file)
        return None
    
    def process_all_months(self):
        """Process all months in the year"""
        extracted_path = self.unzip_files(self.base_path)
        
        if not extracted_path:
            return False
        
        export_path = self.find_export_folder(extracted_path)
        
        if not export_path:
            st.error("❌ Export folder not found")
            return False
        
        month_folders = self.get_month_folders(export_path)
        
        if not month_folders:
            st.error("❌ No month folders found")
            return False
        
        progress_text = st.empty()
        for month in range(1, 13):
            if month in month_folders:
                progress_text.text(f"📊 Processing month {month:02d}...")
                month_path = month_folders[month]['path']
                excel_file = self.find_excel_in_month_folder(month_path)
                
                if excel_file:
                    result = self.process_excel_file(excel_file)
                    if result:
                        self.months_data[month] = result
                    else:
                        self.months_data[month] = {team: {'BM': 0, 'TH': 0, 'PM_CM': 0} for team in self.teams}
                else:
                    self.months_data[month] = {team: {'BM': 0, 'TH': 0, 'PM_CM': 0} for team in self.teams}
            else:
                self.months_data[month] = {team: {'BM': 0, 'TH': 0, 'PM_CM': 0} for team in self.teams}
        
        progress_text.empty()
        return True
    
    def create_visualization(self, selected_team):
        """Create visualization for selected team"""
        months = list(range(1, 13))
        months_labels = [f"Month {m}" for m in months]
        
        bm_values = [self.months_data.get(m, {}).get(selected_team, {}).get('BM', 0) for m in months]
        th_values = [self.months_data.get(m, {}).get(selected_team, {}).get('TH', 0) for m in months]
        pm_cm_values = [self.months_data.get(m, {}).get(selected_team, {}).get('PM_CM', 0) for m in months]
        
        # Title based on selection
        if selected_team == 'All':
            title1 = '📊 Total Cost by 3 Categories (Annual)'
            title2 = '📈 12-Month Total Cost by Category'
        else:
            title1 = f'📊 {selected_team} Cost by 3 Categories (Annual)'
            title2 = f'📈 {selected_team} 12-Month Cost by Category'
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(title1, title2),
            specs=[[{"type": "bar"}], [{"type": "bar"}]],
            vertical_spacing=0.12,
            row_heights=[0.38, 0.62]
        )
        
        # Chart 1: Total by 3 categories
        total_bm = sum(bm_values)
        total_th = sum(th_values)
        total_pm_cm = sum(pm_cm_values)
        
        fig.add_trace(
            go.Bar(
                x=['BM', 'TH', 'PM/CM'],
                y=[total_bm, total_th, total_pm_cm],
                text=[f'${v:,.2f}' for v in [total_bm, total_th, total_pm_cm]],
                textposition='auto',
                textfont=dict(size=16, weight='bold'),
                marker=dict(
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1'],
                    line=dict(color='white', width=3)
                ),
                name='Annual Total',
                showlegend=False,
                width=0.6,
                cliponaxis=False
            ),
            row=1, col=1
        )
        
        # Chart 2: 12-month details
        fig.add_trace(
            go.Bar(
                x=months_labels,
                y=bm_values,
                name='BM',
                marker=dict(color='#FF6B6B', line=dict(color='white', width=1)),
                text=[f'${v:,.2f}' if v > 0 else '' for v in bm_values],
                textposition='outside',
                textfont=dict(size=12),
                hovertemplate='<b>%{x}</b><br>BM: $%{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=months_labels,
                y=th_values,
                name='TH',
                marker=dict(color='#4ECDC4', line=dict(color='white', width=1)),
                text=[f'${v:,.2f}' if v > 0 else '' for v in th_values],
                textposition='outside',
                textfont=dict(size=12),
                hovertemplate='<b>%{x}</b><br>TH: $%{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=months_labels,
                y=pm_cm_values,
                name='PM/CM',
                marker=dict(color='#45B7D1', line=dict(color='white', width=1)),
                text=[f'${v:,.2f}' if v > 0 else '' for v in pm_cm_values],
                textposition='outside',
                textfont=dict(size=12),
                hovertemplate='<b>%{x}</b><br>PM/CM: $%{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
          
        
        fig.update_layout(
            title_text="",
            title_font_size=28,
            title_x=0.5,
            showlegend=True,
            height=1100,
            hovermode='x unified',
            margin=dict(t=120, b=50, l=50, r=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.12,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            plot_bgcolor='rgba(240,240,240,0.5)',
            paper_bgcolor='white'
        )
        
        fig.update_xaxes(title_text="Category", row=1, col=1, tickfont=dict(size=14), title_font=dict(size=16))
        fig.update_xaxes(title_text="Month", row=2, col=1, tickangle=-45, tickfont=dict(size=13), title_font=dict(size=16))
        fig.update_yaxes(title_text="Cost (USD)", row=1, col=1, gridcolor='white', tickfont=dict(size=13), title_font=dict(size=16))
        fig.update_yaxes(title_text="Cost (USD)", row=2, col=1, gridcolor='white', tickfont=dict(size=13), title_font=dict(size=16))
        
        max_value = max(total_bm, total_th, total_pm_cm)
        if max_value > 0:
            fig.update_yaxes(range=[0, max_value * 1.15], row=1, col=1)
        
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(size=18, weight='bold')
        
        return fig


def main_xuatkho():
    st.set_page_config(
        page_title="Warehouse Export Cost Tracking",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .main-header {
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            padding: 15px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stApp {
            background-color: #f8f9fa;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🏭 TOTAL COST DX TRACKING SYSTEM</div>', 
                unsafe_allow_html=True)
    
  
    BASE_PATH = r"   "
    
  
    # Team selector
    selected_team = st.selectbox(
        "Select Team to View Details:",
        ['All', 'Control', 'Assy', 'Process', 'Die cast'],
        index=0,
        help="Select 'All' for total cost or specific team for team cost breakdown"
    )
    
    st.markdown("---")
    
    process_data(BASE_PATH, selected_team)


def process_data(base_path, selected_team):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        if not os.path.exists(base_path):
            st.error(f"❌ Path not found: {base_path}")
            st.info("💡 Please check network connection and folder access permissions.")
            return

        progress_bar.progress(10)
        viz = UnifiedCostVisualization(base_path)
        
        progress_bar.progress(25)
        time.sleep(0.3)
        
        success = viz.process_all_months()
        progress_bar.progress(75)
        
        if not success:
            progress_bar.empty()
            status_text.empty()
            return
        
        status_text.text("🎨 Creating charts...")
        progress_bar.progress(90)
        
        fig = viz.create_visualization(selected_team)
        
        progress_bar.progress(100)
        status_text.text("✅ Complete!")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        
        # Metrics
        st.markdown(f"### 📈 Summary Statistics - {selected_team}")
        col1, col2, col3, col4 = st.columns(4)
        
        total_bm = sum(viz.months_data.get(m, {}).get(selected_team, {}).get('BM', 0) for m in range(1, 13))
        total_th = sum(viz.months_data.get(m, {}).get(selected_team, {}).get('TH', 0) for m in range(1, 13))
        total_pm_cm = sum(viz.months_data.get(m, {}).get(selected_team, {}).get('PM_CM', 0) for m in range(1, 13))
        total_all = total_bm + total_th + total_pm_cm
        
        with col1:
            st.metric("💰 Total BM", f"${total_bm:,.2f}")
        with col2:
            st.metric("🔧 Total TH", f"${total_th:,.2f}")
        with col3:
            st.metric("⚙️ Total PM/CM", f"${total_pm_cm:,.2f}")
        with col4:
            st.metric("📊 Grand Total", f"${total_all:,.2f}")
        
        st.markdown("---")
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison table for all teams
        if selected_team == 'All':
            st.markdown("---")
            st.markdown("### 📊 Team Comparison")
            
            comparison_data = []
            for team in ['Control', 'Assy', 'Process', 'Die cast']:
                team_bm = sum(viz.months_data.get(m, {}).get(team, {}).get('BM', 0) for m in range(1, 13))
                team_th = sum(viz.months_data.get(m, {}).get(team, {}).get('TH', 0) for m in range(1, 13))
                team_pm_cm = sum(viz.months_data.get(m, {}).get(team, {}).get('PM_CM', 0) for m in range(1, 13))
                comparison_data.append({
                    'Team': team,
                    'BM (USD)': f"${team_bm:,.2f}",
                    'TH (USD)': f"${team_th:,.2f}",
                    'PM/CM (USD)': f"${team_pm_cm:,.2f}",
                    'Total (USD)': f"${(team_bm + team_th + team_pm_cm):,.2f}"
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Monthly detail table
        st.markdown("---")
        st.markdown(f"### 📋 {selected_team} - Monthly Detail")
        
        data_table = []
        for month in range(1, 13):
            data = viz.months_data.get(month, {}).get(selected_team, {})
            data_table.append({
                'Month': f'Month {month:02d}',
                'BM (USD)': f"${data.get('BM', 0):,.2f}",
                'TH (USD)': f"${data.get('TH', 0):,.2f}",
                'PM/CM (USD)': f"${data.get('PM_CM', 0):,.2f}",
                'Total (USD)': f"${sum(data.values()):,.2f}"
            })
        
        df_display = pd.DataFrame(data_table)
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=460)
        
        st.markdown("---")
        st.caption(f"⏰ Updated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("💡 Please contact IT for support.")


if __name__ == "__main__":
    main_xuatkho()
