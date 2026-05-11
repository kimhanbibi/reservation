import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime
from pathlib import Path

# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="실험 예약 시스템",
    page_icon="🧪",
    layout="wide"
)

DATA_FILE = Path("reservations.csv")

GROUPS = [f"{i}조" for i in range(1, 11)]
AVAILABLE_TIMES = [
    "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00",
    "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
    "17:00-18:00", "18:00-19:00", "19:00-20:00", "20:00-21:00",
    "21:00-22:00",
]
YEAR = 2026
MIN_DATE = date(YEAR, 5, 1)
MAX_DATE = date(YEAR, 6, 30)
MONTHS = [5, 6]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

# =============================
# CSS
# =============================
st.markdown(
    """
    <style>
    .calendar-title {
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin: 10px 0 20px 0;
    }
    .weekday-box {
        text-align: center;
        font-weight: 700;
        padding: 10px 0;
        background-color: #222832;
        border-radius: 10px;
        margin-bottom: 6px;
    }
    div[data-testid="stButton"] > button {
        width: 100%;
        height: 70px;
        border-radius: 14px;
        font-size: 18px;
        font-weight: 700;
    }
    .legend {
        padding: 12px;
        border-radius: 12px;
        background-color: #1f2937;
        margin-bottom: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# 데이터 함수
# =============================
def load_reservations():
    columns = ["예약ID", "예약시간", "조", "조장명", "예약날짜", "실험시간", "공지사항"]

    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)

        if "예약ID" not in df.columns:
            df.insert(0, "예약ID", range(1, len(df) + 1))

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        df = df[columns]
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        return df

    return pd.DataFrame(columns=columns)


def save_reservations(group, leader_name, reservation_date, reservation_times, notice):
    df = load_reservations()

    next_id = 1 if df.empty else int(df["예약ID"].max()) + 1
    new_rows = []

    for reservation_time in reservation_times:
        new_rows.append({
            "예약ID": next_id,
            "예약시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "조": group,
            "조장명": leader_name,
            "예약날짜": reservation_date.strftime("%Y-%m-%d"),
            "실험시간": reservation_time,
            "공지사항": notice,
        })
        next_id += 1

    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def delete_reservation_ids(reservation_ids):
    df = load_reservations()
    reservation_ids = [int(x) for x in reservation_ids]
    df = df[~df["예약ID"].astype(int).isin(reservation_ids)]
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def replace_reservation_group(old_reservation_ids, group, leader_name, new_date, new_times, notice):
    """선택한 예약 묶음을 삭제하고, 새 날짜/새 시간 묶음으로 다시 저장합니다."""
    delete_reservation_ids(old_reservation_ids)
    save_reservations(group, leader_name, new_date, new_times, notice)


def get_reserved_dates():
    df = load_reservations()
    if df.empty:
        return set()

    valid_dates = df["예약날짜"].dropna().astype(str).unique().tolist()
    return set(valid_dates)


# =============================
# 세션 상태
# =============================
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "selected_month" not in st.session_state:
    st.session_state.selected_month = 5

# =============================
# 화면 시작
# =============================
title_col, notice_col = st.columns([1.4, 1])

with title_col:
    st.title("🧪 실험 예약 시스템")
    st.caption("달력에서 날짜를 누르고, 시간을 선택한 뒤 예약하면 해당 날짜가 파란색으로 표시됩니다.")

with notice_col:
    st.markdown("### 📢 전체 공지사항")
    st.info(
        """
 ### 전체 공지사항

- 장소는 116 입니다
- 21~23일은 철도학회 참석으로 실험 불가능합니다.
- 매주 금요일 9~12시까지는 대학원 수업이라 불가능하고 오후부터 이용 가능합니다.
- 추가 문의사항이 있으면 조교 번호로 연락 및 128로 오세요
        """
    )

left, right = st.columns([2, 1])

# =============================
# 왼쪽: 달력
# =============================
with left:
    st.subheader("1. 날짜 선택")

    month_col1, month_col2 = st.columns(2)
    with month_col1:
        if st.button("2026년 5월", use_container_width=True):
            st.session_state.selected_month = 5
            st.session_state.selected_date = None
    with month_col2:
        if st.button("2026년 6월", use_container_width=True):
            st.session_state.selected_month = 6
            st.session_state.selected_date = None

    selected_month = st.session_state.selected_month
    reserved_dates = get_reserved_dates()

    st.markdown(f"<div class='calendar-title'>{YEAR}년 {selected_month}월</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='legend'>🔵 예약 있음 &nbsp;&nbsp; ✅ 현재 선택한 날짜</div>",
        unsafe_allow_html=True,
    )

    weekday_cols = st.columns(7)
    for i, day_name in enumerate(WEEKDAYS):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-box'>{day_name}</div>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdatescalendar(YEAR, selected_month)

    for week in month_weeks:
        cols = st.columns(7)
        for i, current_day in enumerate(week):
            with cols[i]:
                if current_day.month != selected_month:
                    st.button(" ", key=f"empty-{selected_month}-{current_day}", disabled=True)
                else:
                    date_str = current_day.strftime("%Y-%m-%d")
                    is_reserved = date_str in reserved_dates
                    is_selected = st.session_state.selected_date == current_day

                    label = str(current_day.day)
                    if is_selected:
                        label = f"✅ {current_day.day}"
                    elif is_reserved:
                        label = f"🔵 {current_day.day}"

                    if st.button(label, key=f"day-{date_str}", use_container_width=True):
                        st.session_state.selected_date = current_day

# =============================
# 오른쪽: 새 예약 입력
# =============================
with right:
    st.subheader("2. 조장 정보")

    group = st.selectbox("본인 조", GROUPS)
    leader_name = st.text_input("조장 이름", placeholder="예: 홍길동")

    if leader_name.strip():
        st.success(f"{group} 조장 {leader_name}님")

    st.divider()
    st.subheader("3. 시간 선택")

    if st.session_state.selected_date is None:
        st.warning("먼저 달력에서 날짜를 선택하세요.")
        reservation_times = []
    else:
        st.info(f"선택한 날짜: **{st.session_state.selected_date.strftime('%Y년 %m월 %d일')}**")
        reservation_times = st.multiselect(
            "실험 시간 - 여러 개 선택 가능",
            AVAILABLE_TIMES,
            placeholder="원하는 시간을 모두 선택하세요",
            key="new_reservation_times",
        )

    st.divider()
    st.subheader("4. 공지사항")
    notice = st.text_area(
        "공지사항 또는 전달사항",
        placeholder="예: 장비 사용 전 세팅 필요 / 실험 인원 4명 / 특이사항 없음",
        height=130,
        key="new_notice",
    )

    if st.button("예약하기", type="primary", use_container_width=True):
        if st.session_state.selected_date is None:
            st.error("날짜를 먼저 선택해주세요.")
        elif not leader_name.strip():
            st.error("조장 이름을 입력해주세요.")
        elif not reservation_times:
            st.error("시간을 하나 이상 선택해주세요.")
        else:
            save_reservations(
                group=group,
                leader_name=leader_name.strip(),
                reservation_date=st.session_state.selected_date,
                reservation_times=reservation_times,
                notice=notice.strip(),
            )
            st.success("예약이 완료되었습니다.")
            st.rerun()

# =============================
# 예약 변경 / 취소
# =============================
st.divider()
st.subheader("✏️ 내 예약 변경 또는 취소")

reservations = load_reservations()

if reservations.empty:
    st.info("아직 변경하거나 취소할 예약이 없습니다.")
else:
    edit_col1, edit_col2 = st.columns(2)
    with edit_col1:
        edit_group = st.selectbox("변경할 조 선택", GROUPS, key="edit_group")
    with edit_col2:
        edit_name = st.text_input("조장 이름 확인", placeholder="예약할 때 입력한 이름", key="edit_name")

    my_reservations = reservations[
        (reservations["조"] == edit_group)
        & (reservations["조장명"].astype(str) == edit_name.strip())
    ].copy()

    if edit_name.strip() and my_reservations.empty:
        st.warning("해당 조와 조장명으로 등록된 예약이 없습니다.")

    elif edit_name.strip():
        my_reservations = my_reservations.sort_values(by=["예약날짜", "실험시간"])

        edit_mode = st.radio(
            "변경 방식 선택",
            ["날짜 단위로 한 번에 변경/취소", "시간 1개만 변경/취소"],
            horizontal=True,
        )

        if edit_mode == "날짜 단위로 한 번에 변경/취소":
            date_options = sorted(my_reservations["예약날짜"].astype(str).unique().tolist())
            selected_old_date_str = st.selectbox("변경/취소할 기존 예약 날짜", date_options)

            selected_group_df = my_reservations[
                my_reservations["예약날짜"].astype(str) == selected_old_date_str
            ].sort_values(by="실험시간")

            old_ids = selected_group_df["예약ID"].astype(int).tolist()
            old_times = selected_group_df["실험시간"].astype(str).tolist()
            old_notice = "" if selected_group_df.empty else str(selected_group_df.iloc[0]["공지사항"])
            old_date = datetime.strptime(selected_old_date_str, "%Y-%m-%d").date()

            st.info(f"현재 선택된 예약: **{selected_old_date_str} / {', '.join(old_times)}**")
            st.dataframe(selected_group_df, use_container_width=True, hide_index=True)

            st.markdown("#### 새 예약 내용")
            new_date = st.date_input(
                "새 날짜 - 5월과 6월 모두 이동 가능",
                value=old_date,
                min_value=MIN_DATE,
                max_value=MAX_DATE,
                format="YYYY.MM.DD",
                key=f"bulk_new_date_{selected_old_date_str}",
            )

            new_times = st.multiselect(
                "새 시간 - 여러 개 선택 가능",
                AVAILABLE_TIMES,
                default=[t for t in old_times if t in AVAILABLE_TIMES],
                help="시간을 그대로 두고 날짜만 바꾸려면 기본 선택 그대로 두면 됩니다.",
                key=f"bulk_new_times_{selected_old_date_str}",
            )

            new_notice = st.text_area(
                "새 공지사항",
                value=old_notice if old_notice != "nan" else "",
                height=100,
                key=f"bulk_new_notice_{selected_old_date_str}",
            )

            bulk_col1, bulk_col2 = st.columns(2)
            with bulk_col1:
                if st.button("이 날짜 예약 전체 변경하기", type="primary", use_container_width=True):
                    if not new_times:
                        st.error("새 시간을 하나 이상 선택해주세요.")
                    else:
                        replace_reservation_group(
                            old_reservation_ids=old_ids,
                            group=edit_group,
                            leader_name=edit_name.strip(),
                            new_date=new_date,
                            new_times=new_times,
                            notice=new_notice.strip(),
                        )
                        st.session_state.selected_date = new_date
                        st.session_state.selected_month = new_date.month
                        st.success("선택한 날짜의 예약 전체가 변경되었습니다.")
                        st.rerun()

            with bulk_col2:
                if st.button("이 날짜 예약 전체 취소하기", use_container_width=True):
                    delete_reservation_ids(old_ids)
                    st.session_state.selected_date = None
                    st.warning("선택한 날짜의 예약 전체가 취소되었습니다.")
                    st.rerun()

        else:
            option_labels = []
            option_map = {}
            for _, row in my_reservations.iterrows():
                label = f"ID {row['예약ID']} | {row['예약날짜']} | {row['실험시간']} | {row['공지사항']}"
                option_labels.append(label)
                option_map[label] = int(row["예약ID"])

            selected_option = st.selectbox("변경/취소할 예약 1개 선택", option_labels)
            selected_id = option_map[selected_option]
            selected_row = my_reservations[my_reservations["예약ID"].astype(int) == selected_id].iloc[0]

            old_date = datetime.strptime(str(selected_row["예약날짜"]), "%Y-%m-%d").date()
            old_time = str(selected_row["실험시간"])
            old_notice = str(selected_row["공지사항"])

            st.markdown("#### 새 예약 내용")
            new_date = st.date_input(
                "새 날짜 - 5월과 6월 모두 이동 가능",
                value=old_date,
                min_value=MIN_DATE,
                max_value=MAX_DATE,
                format="YYYY.MM.DD",
                key=f"single_new_date_{selected_id}",
            )

            time_index = AVAILABLE_TIMES.index(old_time) if old_time in AVAILABLE_TIMES else 0
            new_time = st.selectbox("새 시간", AVAILABLE_TIMES, index=time_index, key=f"single_new_time_{selected_id}")

            new_notice = st.text_area(
                "새 공지사항",
                value=old_notice if old_notice != "nan" else "",
                height=100,
                key=f"single_new_notice_{selected_id}",
            )

            single_col1, single_col2 = st.columns(2)
            with single_col1:
                if st.button("선택한 예약 1개 변경하기", type="primary", use_container_width=True):
                    replace_reservation_group(
                        old_reservation_ids=[selected_id],
                        group=edit_group,
                        leader_name=edit_name.strip(),
                        new_date=new_date,
                        new_times=[new_time],
                        notice=new_notice.strip(),
                    )
                    st.session_state.selected_date = new_date
                    st.session_state.selected_month = new_date.month
                    st.success("선택한 예약 1개가 변경되었습니다.")
                    st.rerun()

            with single_col2:
                if st.button("선택한 예약 1개 취소하기", use_container_width=True):
                    delete_reservation_ids([selected_id])
                    st.session_state.selected_date = None
                    st.warning("선택한 예약 1개가 취소되었습니다.")
                    st.rerun()

# =============================
# 전체 예약 현황
# =============================
st.divider()
st.subheader("📋 실험 예약 현황표")

reservations = load_reservations()

if reservations.empty:
    st.info("아직 예약된 실험 일정이 없습니다.")
else:
    reservations = reservations.sort_values(
        by=["예약날짜", "실험시간", "조"],
        ascending=True,
    ).reset_index(drop=True)

    board = reservations.copy()
    board["예약자명"] = board["조"].astype(str) + " " + board["조장명"].astype(str)
    board["분류"] = board["예약날짜"].astype(str) + " / " + board["실험시간"].astype(str)
    board["면 및"] = board["공지사항"].fillna("").astype(str)

    board = board[["예약자명", "분류", "면 및"]]
    board.index = board.index + 1

    st.markdown(
        """
        <style>
        .reservation-board-title {
            background-color: #263238;
            color: white;
            text-align: center;
            font-size: 28px;
            font-weight: 900;
            padding: 16px;
            border-radius: 14px 14px 0 0;
            border: 2px solid #4b5563;
        }
        .reservation-board table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            color: black;
            font-size: 18px;
        }
        .reservation-board th {
            background-color: #f3f4f6;
            color: black;
            text-align: center;
            border: 2px solid #111827;
            padding: 12px;
            font-weight: 800;
        }
        .reservation-board td {
            border: 2px solid #111827;
            padding: 14px;
            min-height: 38px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='reservation-board-title'>실험 예약 현황표</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='reservation-board'>{board.to_html(escape=False)}</div>",
        unsafe_allow_html=True,
    )

    csv = reservations.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="예약 현황 CSV 다운로드",
        data=csv,
        file_name="experiment_reservations.csv",
        mime="text/csv",
        use_container_width=True,
    )

# =============================
# 실행 방법
# =============================
with st.expander("실행 방법 보기"):
    st.code(
        """
pip install streamlit pandas
streamlit run Scheduling.py
""",
        language="bash",
    )



