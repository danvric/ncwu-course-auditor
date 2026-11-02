import pandas as pd
import streamlit as st
import re

# ==========================================
# 1. 页面基本设置
# ==========================================
st.set_page_config(page_title="蹭课小助手", page_icon="🏫", layout="wide")
st.title("🏫 华水江淮校区蹭课系统")

# 初始化视图状态（默认展开）
if 'compact_view' not in st.session_state:
    st.session_state.compact_view = False

# 节次时间映射
PERIOD_TIME = {
    1: "08:00-08:45", 2: "08:55-09:40", 3: "09:55-10:40", 4: "10:50-11:35", 5: "11:45-12:30",
    6: "14:00-14:45", 7: "14:55-15:40", 8: "15:55-16:40", 9: "16:50-17:35", 10: "17:45-18:30",
    11: "19:00-19:45", 12: "19:55-20:40"
}

# ==========================================
# 2. 核心：数据清洗函数
# ==========================================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path, header=1)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(subset=['节次'])
    
    def parse_time(time_str):
        match = re.search(r"([一二三四五六日])\[(\d+)-(\d+)\]", str(time_str))
        if match:
            day_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}
            day = day_map[match.group(1)]
            start_p = int(match.group(2))
            end_p = int(match.group(3))
            return day, list(range(start_p, end_p + 1))
        match_single = re.search(r"([一二三四五六日])\[(\d+)\]", str(time_str))
        if match_single:
            day_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}
            return day_map[match_single.group(1)], [int(match_single.group(2))]
        return None, []

    df[['星期', '节次列表']] = df['节次'].apply(lambda x: pd.Series(parse_time(x)))
    df = df.dropna(subset=['星期'])
    
    def parse_weeks(w_str):
        w_str = str(w_str).strip()
        weeks = []
        try:
            if ',' in w_str:
                for w in w_str.split(','):
                    if '-' in w:
                        start, end = w.split('-')
                        weeks.extend(list(range(int(start), int(end) + 1)))
                    else:
                        weeks.append(int(w))
            elif '-' in w_str:
                start, end = w_str.split('-')
                weeks = list(range(int(start), int(end) + 1))
            else:
                weeks = [int(w_str)]
        except:
            pass
        return weeks
        
    df['周次列表'] = df['周次'].apply(parse_weeks)
    df['教室'] = df['教室'].astype(str).str.replace(r'\[.*?\]', '', regex=True)
    return df

def get_main_course_name(name):
    name = str(name)
    name = re.sub(r'[\(（].*?[\)）]', '', name)
    return name.strip()

# ==========================================
# 3. 你的个人课表字典
# ==========================================
MY_SCHEDULE = {
    1: {3: "工程制图", 4: "工程制图", 5: "工程制图", 6: "高数", 7: "高数/劳动", 8: "Python", 9: "Python", 10: "Python", 11: "Python", 12: "Python"},
    2: {3: "高数", 4: "高数", 6: "形策/思政", 7: "形策/思政", 8: "外语", 9: "外语", 10: "外语", 11: "劳动教育", 12: "劳动教育"},
    3: {3: "体育", 4: "体育", 6: "Python/思政", 7: "Python/思政", 8: "工程制图", 9: "工程制图", 10: "工程制图", 11: "核科学", 12: "核科学"},
    4: {1: "外语/Python", 2: "外语/Python", 3: "形策/思政", 4: "形策/思政", 5: "形策/思政", 6: "高数", 7: "高数", 8: "核科学", 9: "核科学", 11: "军理", 12: "军理"},
    5: {3: "高数", 4: "高数", 5: "高数", 8: "核科学", 9: "核科学", 10: "核科学", 11: "军理", 12: "军理"},
    6: {}, 
    7: {}  
}

# ==========================================
# 4. 提取数据供下拉框使用
# ==========================================
try:
    df = load_data("教室课表.xlsx")
    all_courses = sorted(df['课程名称'].dropna().unique().tolist())
    my_course_main_names = set()
    for day_dict in MY_SCHEDULE.values():
        for course_str in day_dict.values():
            for c in course_str.split('/'):
                my_course_main_names.add(get_main_course_name(c))
    my_courses_list = sorted(list(my_course_main_names))
except Exception as e:
    st.error(f"读取数据失败：{e}")
    st.stop()

# ==========================================
# 5. 网页交互界面
# ==========================================
st.sidebar.header("筛选条件")

skip_courses = st.sidebar.multiselect(
    "🏃‍♂️ 选择要旷掉的课 (按主干名屏蔽)",
    options=my_courses_list,
    default=[]
)
if skip_courses:
    st.sidebar.warning(f"⚠️ 已屏蔽：{', '.join(skip_courses)}")

selected_courses = st.sidebar.multiselect(
    "🔍 选择感兴趣的课程 (可搜索、可多选)",
    options=all_courses,
    default=[]
)

week_options = list(range(1, 19))
selected_weeks = st.sidebar.multiselect(
    "📅 选择查看哪几周",
    options=week_options,
    default=[8]
)

weekday_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}
selected_days = st.sidebar.multiselect(
    "📆 选择星期几",
    options=list(weekday_map.keys()),
    format_func=lambda x: weekday_map[x],
    default=[3, 5]
)

time_range = st.sidebar.slider("⏰ 查看哪几节", 1, 12, (6, 10))

hide_conflicts = st.sidebar.checkbox("🙈 隐藏与我课表冲突的课程", value=False)

# ==========================================
# 6. 筛选与展示逻辑
# ==========================================
if not selected_weeks or not selected_days:
    st.warning("请至少在左侧选择一周和一天！")
else:
    # 顶部控制栏
    col_ctrl1, col_ctrl2, _ = st.columns([1, 1, 4])
    with col_ctrl1:
        if st.button("📖 一键展开所有", use_container_width=True):
            st.session_state.compact_view = False
            st.rerun()
    with col_ctrl2:
        if st.button("📑 一键收起所有", use_container_width=True):
            st.session_state.compact_view = True
            st.rerun()
            
    st.write("---")

    for day in selected_days:
        st.header(f"📅 {weekday_map[day]}")
        
        df_day = df[df['星期'] == day]
        df_day = df_day[df_day['周次列表'].apply(lambda w: any(sel_w in w for sel_w in selected_weeks))]
        df_day = df_day[df_day['节次列表'].apply(lambda p: any(x in range(time_range[0], time_range[1]+1) for x in p))]
        
        if selected_courses:
            df_day = df_day[df_day['课程名称'].isin(selected_courses)]
            
        if df_day.empty:
            st.info("今天没有符合条件的课程~")
            continue

        df_day = df_day.drop_duplicates(subset=['课程名称', '教师', '节次'])
        count_shown = 0
        
        for index, row in df_day.iterrows():
            target_main_name = get_main_course_name(row['课程名称'])
            
            is_skipped_course = any(skip_c in target_main_name for skip_c in skip_courses)
            if is_skipped_course:
                continue

            periods = row['节次列表']
            start_p, end_p = periods[0], periods[-1]
            
            # 冲突检测
            is_conflict = False
            conflict_course = ""
            for p in periods:
                if p in MY_SCHEDULE[day]:
                    my_course_name = MY_SCHEDULE[day][p]
                    my_course_main = get_main_course_name(my_course_name)
                    is_my_course_skipped = any(skip_c in my_course_main for skip_c in skip_courses)
                    if not is_my_course_skipped:
                        is_conflict = True
                        conflict_course = my_course_name
                        break
            
            if hide_conflicts and is_conflict:
                continue
                
            count_shown += 1
            
            # ==========================================
            # 视图渲染：收起模式 vs 展开模式
            # ==========================================
            if st.session_state.compact_view:
                # 收起模式：单行紧凑排版
                with st.container(border=True):
                    c_info, c_status = st.columns([8, 2])
                    with c_info:
                        # 用颜色标记课程名
                        st.markdown(f"**{row['课程名称']}** &nbsp;|&nbsp; 👨‍🏫 {row['教师']} &nbsp;|&nbsp; 🏢 {row['教室']} &nbsp;|&nbsp; ⏰ 第 {start_p}-{end_p} 节")
                    with c_status:
                        if is_conflict:
                            st.caption(f"❌ 冲突")
                        else:
                            st.caption(f"✅ 空闲")
            else:
                # 展开模式：完整卡片
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.subheader(f"📚 {row['课程名称']}")
                        st.write(f"👨‍🏫 **教师**：{row['教师']} | 🏢 **教室**：{row['教室']}")
                        st.write(f"👥 **班级**：{row.get('行政班级', '未知班级')}")
                        st.write(f"⏰ **时间**：第 {start_p}-{end_p} 节 ({PERIOD_TIME.get(start_p, '')} 开始)")
                        
                        show_weeks = [w for w in row['周次列表'] if w in selected_weeks]
                        st.caption(f"🗓️ 选中周次内的上课周：{show_weeks}")
                        
                    with col2:
                        if is_conflict:
                            st.error(f"❌ 时间冲突\n(你有: {conflict_course})")
                        else:
                            st.success("✅ 时间空闲\n(可以去蹭!)")
        
        if count_shown == 0:
            st.info("这个时间段没有（或已被旷课屏蔽）的课程~")
        st.markdown("<br>", unsafe_allow_html=True) # 每天之间加点间距