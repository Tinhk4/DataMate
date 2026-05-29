from __future__ import annotations

import io

import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.express as px
import plotly.io as pio
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st


PALETTE = [
    "#7C5CFF",
    "#22C55E",
    "#06B6D4",
    "#F97316",
    "#E11D48",
    "#EAB308",
]


def _apply_dashboard_style() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
            }
            .dm-hero {
                padding: 1.25rem 1.4rem;
                border-radius: 18px;
                background: linear-gradient(135deg, rgba(124,92,255,0.14), rgba(6,182,212,0.10));
                border: 1px solid rgba(255,255,255,0.08);
                margin-bottom: 1rem;
            }
            .dm-hero h1 {
                margin: 0;
                font-size: 2rem;
            }
            .dm-hero p {
                margin: 0.35rem 0 0 0;
                color: rgba(255,255,255,0.72);
                font-size: 0.95rem;
            }
            .dm-card {
                padding: 1rem 1.05rem;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.08);
                background: rgba(255,255,255,0.03);
                box-shadow: 0 8px 24px rgba(0,0,0,0.18);
                height: 100%;
            }
            .dm-card h3 {
                margin: 0 0 0.45rem 0;
                font-size: 0.92rem;
                color: rgba(255,255,255,0.72);
                font-weight: 600;
                letter-spacing: 0.02em;
            }
            .dm-card .value {
                font-size: 1.6rem;
                font-weight: 700;
                line-height: 1.1;
            }
            .dm-card .caption {
                margin-top: 0.35rem;
                color: rgba(255,255,255,0.62);
                font-size: 0.82rem;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.4rem;
            }
            .stTabs [data-baseweb="tab"] {
                border-radius: 999px;
                padding: 0.5rem 0.95rem;
            }
            .stPlotlyChart {
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid rgba(255,255,255,0.08);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_dataframe(uploaded_file) -> pd.DataFrame | None:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    return st.session_state.get("df")


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


def _format_card(title: str, value: str, caption: str) -> str:
    return f"""
    <div class="dm-card">
        <h3>{title}</h3>
        <div class="value">{value}</div>
        <div class="caption">{caption}</div>
    </div>
    """


def _plotly_export_bytes(fig, filename_base: str) -> tuple[bytes, bytes | None]:
    html_bytes = fig.to_html(include_plotlyjs="cdn").encode("utf-8")
    png_bytes: bytes | None
    try:
        png_bytes = pio.to_image(fig, format="png", scale=2)
    except Exception:
        png_bytes = None
    return html_bytes, png_bytes


def _plotly_image_bytes(fig, image_format: str) -> bytes | None:
    try:
        return pio.to_image(fig, format=image_format, scale=2)
    except Exception:
        return None


def _matplotlib_image_bytes(fig, image_format: str) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format=image_format, bbox_inches="tight", dpi=200)
    buffer.seek(0)
    return buffer.getvalue()


def _render_header(df: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="dm-hero">
            <h1>Interactive Visualization Studio</h1>
            <p>Build clean charts with Plotly and exploratory views with Seaborn, all in a single dashboard.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = [
        ("Rows", f"{df.shape[0]:,}", "Total records loaded"),
        ("Columns", f"{df.shape[1]:,}", "Fields available for analysis"),
        ("Missing Cells", f"{int(df.isna().sum().sum()):,}", "Null values across the dataset"),
        ("Duplicate Rows", f"{int(df.duplicated().sum()):,}", "Potential repeated records"),
    ]

    cols = st.columns(4)
    for column, (title, value, caption) in zip(cols, metrics):
        with column:
            st.markdown(_format_card(title, value, caption), unsafe_allow_html=True)


def _render_dataset_snapshot(df: pd.DataFrame) -> None:
    left, right = st.columns([1.3, 0.9])
    with left:
        st.subheader("Preview")
        st.dataframe(df.head(15), use_container_width=True)
    with right:
        st.subheader("Column Types")
        type_summary = pd.DataFrame(
            {
                "Numeric": [len(_numeric_columns(df))],
                "Categorical": [len(_categorical_columns(df))],
                "Datetime": [len(df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns)],
                "Other": [df.shape[1] - len(_numeric_columns(df)) - len(_categorical_columns(df))],
            }
        )
        st.dataframe(type_summary, use_container_width=True, hide_index=True)

        st.subheader("Quick Summary")
        summary = df.describe(include="all").transpose().reset_index().rename(columns={"index": "column"})
        st.dataframe(summary, use_container_width=True)


def _render_overview(df: pd.DataFrame) -> None:
    _render_header(df)
    _render_dataset_snapshot(df)


def _render_plotly_chart(df: pd.DataFrame) -> None:
    numeric_cols = _numeric_columns(df)
    categorical_cols = _categorical_columns(df)

    st.subheader("Plotly Builder")
    st.caption("Use the controls below to compose a polished interactive chart.")

    chart_type = st.selectbox(
        "Chart type",
        ["Scatter", "Line", "Bar", "Histogram", "Box", "Pie"],
        key="plotly_chart_type",
    )

    control_left, control_right = st.columns(2)

    if chart_type in {"Scatter", "Line", "Bar", "Box"}:
        x_col = control_left.selectbox("X-axis", df.columns, key=f"x_{chart_type}")
        y_default = numeric_cols[0] if numeric_cols else df.columns[0]
        y_col = control_right.selectbox(
            "Y-axis",
            df.columns,
            index=df.columns.get_loc(y_default) if y_default in df.columns else 0,
            key=f"y_{chart_type}",
        )

        if chart_type in {"Scatter", "Line", "Box"} and not is_numeric_dtype(df[y_col]):
            st.warning("Cột Y nên là dạng số cho chart này. Vui lòng chọn cột numeric.")
            return

        try:
            if chart_type == "Scatter":
                color_col = st.selectbox("Color", ["None", *categorical_cols], key="scatter_color")
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=None if color_col == "None" else color_col,
                    color_discrete_sequence=PALETTE,
                    template="plotly_dark",
                    title=f"{y_col} vs {x_col}",
                )
            elif chart_type == "Line":
                color_col = st.selectbox("Color", ["None", *categorical_cols], key="line_color")
                fig = px.line(
                    df,
                    x=x_col,
                    y=y_col,
                    color=None if color_col == "None" else color_col,
                    markers=True,
                    color_discrete_sequence=PALETTE,
                    template="plotly_dark",
                    title=f"{y_col} over {x_col}",
                )
            elif chart_type == "Bar":
                agg_fn = st.selectbox("Aggregation", ["sum", "mean", "median", "count"], key="bar_agg")

                if agg_fn == "count":
                    grouped = df.groupby(x_col, dropna=False).size().reset_index(name="value")
                    y_label = "count"
                else:
                    if not is_numeric_dtype(df[y_col]):
                        st.warning("Với Aggregation là sum/mean/median, cột Y phải là dạng số.")
                        return
                    grouped = df.groupby(x_col, dropna=False).agg(value=(y_col, agg_fn)).reset_index()
                    y_label = f"{agg_fn}({y_col})"

                fig = px.bar(
                    grouped,
                    x=x_col,
                    y="value",
                    color_discrete_sequence=[PALETTE[0]],
                    template="plotly_dark",
                    title=f"{y_label} by {x_col}",
                    labels={"value": y_label},
                )
            else:
                fig = px.box(
                    df,
                    x=x_col,
                    y=y_col,
                    color=x_col if x_col in categorical_cols else None,
                    color_discrete_sequence=PALETTE,
                    template="plotly_dark",
                    title=f"Distribution of {y_col} by {x_col}",
                )
        except Exception as exc:
            st.warning(f"Không thể tạo chart với lựa chọn hiện tại: {exc}")
            return

    elif chart_type == "Histogram":
        x_col = st.selectbox("Numeric column", numeric_cols or df.columns.tolist(), key="hist_x")
        nbins = st.slider("Bins", min_value=10, max_value=80, value=30, step=5, key="hist_bins")
        fig = px.histogram(
            df,
            x=x_col,
            nbins=nbins,
            color_discrete_sequence=[PALETTE[2]],
            template="plotly_dark",
            title=f"Distribution of {x_col}",
        )

    else:
        if chart_type == "Pie":
            label_col = st.selectbox("Labels", categorical_cols or df.columns.tolist(), key="pie_label")
            value_col = st.selectbox("Values", numeric_cols or df.columns.tolist(), key="pie_value")
            if not is_numeric_dtype(df[value_col]):
                st.warning("Cột Values của Pie chart phải là dạng số.")
                return
            try:
                pie_df = df.groupby(label_col, dropna=False).agg(value=(value_col, "sum")).reset_index()
                fig = px.pie(
                    pie_df,
                    names=label_col,
                    values="value",
                    color_discrete_sequence=PALETTE,
                    template="plotly_dark",
                    title=f"Share of {value_col} by {label_col}",
                    labels={"value": value_col},
                )
            except Exception as exc:
                st.warning(f"Không thể tạo Pie chart với lựa chọn hiện tại: {exc}")
                return
        else:
            fig = px.histogram(
                df,
                x=numeric_cols[0] if numeric_cols else df.columns[0],
                color_discrete_sequence=[PALETTE[3]],
                template="plotly_dark",
            )

    fig.update_layout(
        height=650,
        margin=dict(l=10, r=10, t=70, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(size=13),
    )

    filename_base = f"plotly_{chart_type.lower()}"
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Tải chart**")
    download_left, download_right = st.columns([0.28, 0.72], vertical_alignment="center")
    with download_left:
        image_choice = st.selectbox(
            "Định dạng",
            ["PNG", "JPG"],
            index=0,
            key=f"dl_plotly_fmt_{chart_type}",
            label_visibility="collapsed",
        )
    with download_right:
        image_format = "png" if image_choice == "PNG" else "jpeg"
        image_bytes = _plotly_image_bytes(fig, image_format)
        if image_bytes is None:
            st.info("Không thể xuất ảnh (cần `kaleido`).")
        else:
            file_ext = "png" if image_choice == "PNG" else "jpg"
            mime = "image/png" if image_choice == "PNG" else "image/jpeg"
            st.download_button(
                "Tải chart",
                data=image_bytes,
                file_name=f"{filename_base}.{file_ext}",
                mime=mime,
                use_container_width=True,
                key=f"dl_plotly_img_{chart_type}",
            )


def _render_seaborn_chart(df: pd.DataFrame) -> None:
    numeric_cols = _numeric_columns(df)
    st.subheader("Seaborn Lab")
    st.caption("A compact exploratory area for correlation and distribution checks.")

    if not numeric_cols:
        st.info("Seaborn correlation view needs numeric columns.")
        return

    chart_mode = st.selectbox(
        "Seaborn chart",
        ["Correlation heatmap", "Distribution", "Pairplot"],
        key="seaborn_mode",
    )

    if chart_mode == "Correlation heatmap":
        corr = df[numeric_cols].corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(min(14, 1 + len(numeric_cols) * 0.9), min(10, 1 + len(numeric_cols) * 0.8)))
        sns.heatmap(corr, annot=True, cmap="mako", center=0, fmt=".2f", linewidths=0.5, ax=ax)
        ax.set_title("Correlation heatmap")
        st.pyplot(fig, clear_figure=True)

        st.markdown("**Tải chart**")
        download_left, download_right = st.columns([0.28, 0.72], vertical_alignment="center")
        with download_left:
            image_choice = st.selectbox(
                "Định dạng",
                ["PNG", "JPG"],
                index=0,
                key="dl_seaborn_corr_fmt",
                label_visibility="collapsed",
            )
        with download_right:
            image_format = "png" if image_choice == "PNG" else "jpeg"
            file_ext = "png" if image_choice == "PNG" else "jpg"
            mime = "image/png" if image_choice == "PNG" else "image/jpeg"
            st.download_button(
                "Tải chart",
                data=_matplotlib_image_bytes(fig, image_format),
                file_name=f"seaborn_correlation_heatmap.{file_ext}",
                mime=mime,
                use_container_width=True,
                key="dl_seaborn_corr_img",
            )

    elif chart_mode == "Distribution":
        target_col = st.selectbox("Numeric column", numeric_cols, key="seaborn_dist_col")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(df[target_col].dropna(), kde=True, color="#4C78A8", ax=ax)
        ax.set_title(f"Distribution of {target_col}")
        st.pyplot(fig, clear_figure=True)

        st.markdown("**Tải chart**")
        download_left, download_right = st.columns([0.28, 0.72], vertical_alignment="center")
        with download_left:
            image_choice = st.selectbox(
                "Định dạng",
                ["PNG", "JPG"],
                index=0,
                key=f"dl_seaborn_dist_fmt_{target_col}",
                label_visibility="collapsed",
            )
        with download_right:
            image_format = "png" if image_choice == "PNG" else "jpeg"
            file_ext = "png" if image_choice == "PNG" else "jpg"
            mime = "image/png" if image_choice == "PNG" else "image/jpeg"
            st.download_button(
                "Tải chart",
                data=_matplotlib_image_bytes(fig, image_format),
                file_name=f"seaborn_distribution_{target_col}.{file_ext}",
                mime=mime,
                use_container_width=True,
                key=f"dl_seaborn_dist_img_{target_col}",
            )

    else:
        pair_cols = st.multiselect(
            "Columns for pairplot",
            numeric_cols,
            default=numeric_cols[: min(4, len(numeric_cols))],
            key="seaborn_pair_cols",
        )
        if len(pair_cols) < 2:
            st.info("Select at least two numeric columns for a pairplot.")
            return

        pairplot_df = df[pair_cols].dropna().sample(min(500, len(df)), random_state=42)
        plot = sns.pairplot(pairplot_df, corner=True, diag_kind="hist")
        st.pyplot(plot.fig, clear_figure=True)

        st.markdown("**Tải chart**")
        download_left, download_right = st.columns([0.28, 0.72], vertical_alignment="center")
        with download_left:
            image_choice = st.selectbox(
                "Định dạng",
                ["PNG", "JPG"],
                index=0,
                key="dl_seaborn_pair_fmt",
                label_visibility="collapsed",
            )
        with download_right:
            image_format = "png" if image_choice == "PNG" else "jpeg"
            file_ext = "png" if image_choice == "PNG" else "jpg"
            mime = "image/png" if image_choice == "PNG" else "image/jpeg"
            st.download_button(
                "Tải chart",
                data=_matplotlib_image_bytes(plot.fig, image_format),
                file_name=f"seaborn_pairplot.{file_ext}",
                mime=mime,
                use_container_width=True,
                key="dl_seaborn_pair_img",
            )


def main() -> None:
    st.set_page_config(
        page_title="Interactive Visualization Tool",
        page_icon="📈",
        layout="wide",
    )
    _apply_dashboard_style()

    st.title("📈 Interactive Visualization Tool")
    st.caption("A cleaner plotting workspace with Plotly and Seaborn inside Streamlit.")

    with st.sidebar:
        st.subheader("Data Source")
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if st.button("Clear dataset"):
            st.session_state.pop("df", None)
            st.rerun()

        if st.session_state.get("df") is not None:
            st.divider()
            st.subheader("Active Dataset")
            st.caption(f"Rows: {st.session_state.df.shape[0]:,}")
            st.caption(f"Columns: {st.session_state.df.shape[1]:,}")

    df = _load_dataframe(uploaded_file)
    if df is None:
        st.info("Upload a CSV file to start visualizing your data.")
        return

    st.session_state.df = df

    overview_tab, plotly_tab, seaborn_tab = st.tabs(["Overview", "Plotly", "Seaborn"])

    with overview_tab:
        _render_overview(df)

    with plotly_tab:
        _render_plotly_chart(df)

    with seaborn_tab:
        _render_seaborn_chart(df)


if __name__ == "__main__":
    main()
