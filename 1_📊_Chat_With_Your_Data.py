import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from dotenv import load_dotenv

from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from src.logger.base import BaseLogger
from src.models.llms import load_llms_model
from src.utils import execute_plt_code

# Load the environment variables
load_dotenv()

logger = BaseLogger()
MODEL_NAME = "gemini-1.5-pro"
MODEL_NAME = "gpt-4o"


AGENT_PREFIX_VI = """Bạn là trợ lý phân tích dữ liệu cho ứng dụng DataMate.

Quy tắc bắt buộc:
- Luôn trả lời bằng TIẾNG VIỆT, kể cả khi câu hỏi có tiếng Anh.
- Trả lời ngắn gọn, đúng trọng tâm.
- Khi nêu kết quả thống kê, ưu tiên bảng/bullet rõ ràng.
"""


def _matplotlib_image_bytes(fig, image_format: str) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format=image_format, bbox_inches="tight", dpi=200)
    buffer.seek(0)
    return buffer.getvalue()


def _wrap_query_vi(query: str) -> str:
    instruction = (
        "Bạn là trợ lý phân tích dữ liệu. "
        "Luôn trả lời bằng TIẾNG VIỆT. "
        "Giữ nguyên tên cột/giá trị dữ liệu (không dịch city/segment/...). "
        "Nếu cần đưa code Python để vẽ biểu đồ, chỉ trả về code (không thêm giải thích ngoài code)."
    )
    return f"{instruction}\n\nCâu hỏi: {query}".strip()


def init_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "df" not in st.session_state:
        st.session_state.df = None
    if "file_name" not in st.session_state:
        st.session_state.file_name = None
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "plot_download_index" not in st.session_state:
        st.session_state.plot_download_index = 0
    if "df_version" not in st.session_state:
        st.session_state.df_version = 0
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "agent_model" not in st.session_state:
        st.session_state.agent_model = None
    if "agent_df_version" not in st.session_state:
        st.session_state.agent_df_version = None
    if "agent_prefix_version" not in st.session_state:
        st.session_state.agent_prefix_version = None

def process_query(agent, query):
    response = agent(_wrap_query_vi(query))
    print("*"*20)
    print(response)
    print("*"*20)
    try:
        response_code = response['intermediate_steps'][-1][0].tool_input
    except:
        response_code = None

    if response_code and (("plt" in response_code) or ("plot" in response_code)):
        st.write("### Vẽ biểu đồ ###")
        st.write(response['output'])
        fig = execute_plt_code(response_code, st.session_state.df)
        if fig is not None:
            idx = st.session_state.plot_download_index
            st.session_state.plot_download_index += 1
            st.pyplot(fig)

            st.markdown("**Tải chart**")
            download_left, download_right = st.columns([0.28, 0.72], vertical_alignment="center")
            with download_left:
                image_choice = st.selectbox(
                    "Định dạng",
                    ["PNG", "JPG"],
                    index=0,
                    key=f"dl_chat_fmt_{idx}",
                    label_visibility="collapsed",
                )
            with download_right:
                image_format = "png" if image_choice == "PNG" else "jpeg"
                file_ext = "png" if image_choice == "PNG" else "jpg"
                mime = "image/png" if image_choice == "PNG" else "image/jpeg"
                st.download_button(
                    "Tải chart",
                    data=_matplotlib_image_bytes(fig, image_format),
                    file_name=f"chat_chart_{idx}.{file_ext}",
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_chat_btn_{idx}",
                )
        st.write("**Executed code:**")
        st.code(response_code)
        str_display = response['output'] + "\n" + f"```python\n{response_code}```"
        st.session_state.history.append((query, str_display))

    else:
        st.write(response['output'])
        st.session_state.history.append((query, response['output']))

def display_chat_history():
    st.write("### Lịch sử chat 🕵️‍♂️ ###")
    for i, (query, response) in enumerate(st.session_state.history):
        st.write(f"**Câu hỏi {i+1}:** {query}")
        st.write(f"**Trả lời:** {response}")

def main():

    # set up streamlit interface
    st.set_page_config(
        page_title="DataMate - Your Data Analysis Assistant", 
        page_icon="📊", 
        layout="centered", # Options: "centered" or "wide"
        initial_sidebar_state="expanded",  # Options: "collapsed", "expanded"
    )
    st.header("DataMate📊-Your Data Analysis Assistant🧠")
    st.write("### 🤖Welcome to DataMate! Let's start analyzing your data! ###")
    init_state()

    # Dropdown for model selection
    model_options = ["gpt-4o", "gemini-1.5-pro", "gemini-2.0-flash-exp", "llama", "other"]
    selected_model = st.selectbox("Select the model to use:", model_options)

    # If 'other' is selected, show a text input to enter a custom model name
    if selected_model == "other":
        selected_model = st.text_input("Enter the name of the custom model:")

    # Load llms model based on selection
    llm = load_llms_model(selected_model)
    logger.info(f"### Successfully loaded the model: {selected_model} !###")

    # Upload CSV file and chat history live in the sidebar tabs
    upload_tab, history_tab = st.sidebar.tabs(["Upload CSV", "Chat History"])

    with upload_tab:
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"], key="chat_csv_uploader")

        if st.session_state.get("df") is not None:
            st.caption(f"Current dataset: {st.session_state.get('file_name') or 'Loaded dataset'}")
            if st.button("Clear dataset", key="chat_clear_dataset"):
                st.session_state.df = None
                st.session_state.file_name = None
                st.session_state.file_uploaded = False
                st.session_state.df_version += 1
                st.session_state.agent = None
                st.rerun()

    with history_tab:
        display_chat_history()

    # Read the CSV file (or reuse existing dataset from other tabs/pages)
    if uploaded_file is not None:
        st.session_state.file_name = uploaded_file.name
        st.session_state.file_uploaded = True
        st.session_state.df = pd.read_csv(uploaded_file)
        st.session_state.df_version += 1
        st.session_state.agent = None

    if st.session_state.get("df") is None:
        st.info("Upload a CSV file to start chatting with your data.")
        return

    st.write("### Data Preview ###", st.session_state.df.head())

    # Create or reuse cached data analysis agent
    if (
        st.session_state.agent is None
        or st.session_state.agent_model != selected_model
        or st.session_state.agent_df_version != st.session_state.df_version
        or st.session_state.agent_prefix_version != "vi"
    ):
        st.session_state.agent = create_pandas_dataframe_agent(
            llm=llm,
            df=st.session_state.df,
            agent_type="zero-shot-react-description",
            prefix=AGENT_PREFIX_VI,
            allow_dangerous_code=True,
            verbose=True,
            return_intermediate_steps=True,
        )
        st.session_state.agent_model = selected_model
        st.session_state.agent_df_version = st.session_state.df_version
        st.session_state.agent_prefix_version = "vi"
        logger.info("### Successfully loaded data analysis agent! ###")

    # Input query and process the query
    query = st.text_input("Nhập câu hỏi của bạn:")
    if st.button("Run query"):
        with st.spinner("Processing your question..."):
            process_query(st.session_state.agent, query)

if __name__ == "__main__":
    main()
