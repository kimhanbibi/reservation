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

# =============================
# GitHub / Streamlit Cloud 배포용 경로 설정
# =============================
# 로컬 실행과 GitHub 배포 환경 모두에서 reservations.csv를
# 현재 파이썬 파일과 같은 폴더에 저장하도록 설정합니다.
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "reservations.csv"

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
        try:
            df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            return df

        if df.empty:
            return pd.DataFrame(columns=columns)

        if "예약ID" not in df.columns:
            df.insert(0, "예약ID", range(1, len(df) + 1))

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        df = df[columns]
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        return df

    df = pd.DataFrame(columns=columns)
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
        **전체공지사항**
        
        - 실험장소는 116 강의실입니다
        - 5월21~23일 철도학회 일정으로 실험 불가합니다
        - 매주 금요일 116에서 대학원 수업이 9:00~12:00까지 진행되니 금요일에 하실 학생은 오후에 이용바랍니다
        - 실험종료일은 6/4일입니다
        - 궁금한사항 조교:김한비 또는 128강의실로오세요
        """
    )

# =============================
# 1. 조장 정보
# =============================
st.divider()
st.subheader("1. 조장 정보")

group = st.selectbox("본인 조", GROUPS)
leader_name = st.text_input("조장 이름", placeholder="예: 홍길동")

if leader_name.strip():
    st.success(f"{group} 조장 {leader_name}님")

# =============================
# 2. 날짜 선택 / 3. 시간 선택
# =============================
st.divider()
left, right = st.columns([1, 1])

with left:
    st.subheader("2. 날짜 선택")

    selected_month = st.selectbox(
        "월 선택",
        MONTHS,
        format_func=lambda month: f"2026년 {month}월",
    )

    if selected_month == 5:
        min_day = date(YEAR, 5, 1)
        max_day = date(YEAR, 5, 31)
    else:
        min_day = date(YEAR, 6, 1)
        max_day = date(YEAR, 6, 30)
    
    day_options = [
    date(YEAR, selected_month, day)
    for day in range(1, max_day.day + 1)
]

    selected_date = st.selectbox(
    "실험 날짜 선택",
    day_options,
    format_func=lambda d: d.strftime("%Y년 %m월 %d일"),
)

    st.session_state.selected_month = selected_month
    st.session_state.selected_date = selected_date

    reserved_dates = get_reserved_dates()
    selected_date_str = selected_date.strftime("%Y-%m-%d")

    if selected_date_str in reserved_dates:
        st.info("🔵 이 날짜에는 이미 예약이 있습니다.")
    else:
        st.success("✅ 선택 가능한 날짜입니다.")

with right:
    st.subheader("3. 시간 선택")

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
        if not leader_name.strip():
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
            change_date_options = [
                date(YEAR, 5, day) for day in range(1, 32)
            ] + [
                date(YEAR, 6, day) for day in range(1, 31)
            ]

            old_date_index = change_date_options.index(old_date) if old_date in change_date_options else 0

            new_date = st.selectbox(
                "새 날짜 - 5월과 6월 모두 이동 가능",
                change_date_options,
                index=old_date_index,
                format_func=lambda d: d.strftime("%Y년 %m월 %d일"),
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
            change_date_options = [
                date(YEAR, 5, day) for day in range(1, 32)
            ] + [
                date(YEAR, 6, day) for day in range(1, 31)
            ]

            old_date_index = change_date_options.index(old_date) if old_date in change_date_options else 0

            new_date = st.selectbox(
                "새 날짜 - 5월과 6월 모두 이동 가능",
                change_date_options,
                index=old_date_index,
                format_func=lambda d: d.strftime("%Y년 %m월 %d일"),
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

    st.markdown("### 🗑️ 예약 선택 삭제")

    delete_options = []

    for _, row in reservations.iterrows():
        label = (
            f"ID {row['예약ID']} | "
            f"{row['조']} | "
            f"{row['조장명']} | "
            f"{row['예약날짜']} | "
            f"{row['실험시간']}"
        )
        delete_options.append(label)

    selected_delete_labels = st.multiselect(
        "삭제할 예약을 선택하세요",
        delete_options,
        placeholder="삭제할 예약 선택"
    )

    if st.button("선택한 예약 삭제하기", type="secondary", use_container_width=True):
        if not selected_delete_labels:
            st.warning("삭제할 예약을 먼저 선택해주세요.")
        else:
            delete_ids = [
                int(label.split("|")[0].replace("ID", "").strip())
                for label in selected_delete_labels
            ]

            delete_reservation_ids(delete_ids)
            st.success("선택한 예약이 삭제되었습니다.")
            st.rerun()

    st.divider()

    # 표시용 테이블 생성
    board = reservations.copy()

    board["예약자"] = (
        board["조"].astype(str)
        + " / "
        + board["조장명"].astype(str)
    )

    board["예약일시"] = (
        board["예약날짜"].astype(str)
        + " / "
        + board["실험시간"].astype(str)
    )

    board["공지사항"] = (
        board["공지사항"]
        .fillna("")
        .astype(str)
        .str.replace("\n", " ")
    )

    board = board[["예약자", "예약일시", "공지사항"]]
    board.index = board.index + 1

    st.markdown(
        """
        <style>
        .reservation-board-title {
            background-color: #1f2937;
            color: white;
            text-align: center;
            font-size: 28px;
            font-weight: 800;
            padding: 16px;
            border-radius: 14px 14px 0 0;
            margin-top: 10px;
        }

        .reservation-board table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            color: black;
            font-size: 17px;
        }

        .reservation-board th {
            background-color: #f3f4f6;
            border: 1px solid #d1d5db;
            padding: 12px;
            text-align: center;
            font-weight: 700;
        }

        .reservation-board td {
            border: 1px solid #d1d5db;
            padding: 12px;
            vertical-align: middle;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='reservation-board-title'>실험 예약 현황표</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='reservation-board'>{board.to_html(escape=False)}</div>",
        unsafe_allow_html=True,
    )




