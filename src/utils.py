import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import re

def execute_plt_code(code: str, df: pd.DataFrame):
    
    try:
        print("------start execute_plt_code------")
        message = AIMessage(content=code)
        output_parser = StrOutputParser()
        code = output_parser.parse(re.sub(r'```python\n|```', '', message.content).strip()).replace("`", "").replace("Observ","")
        # code = output_parser.invoke(message)
        local_vars = {
            "plt": plt,
            "df": df,
            "sns": sns,
        }
        print("_____code______")
        print(code)
        print("___________")
        compiled_code = compile(code, "<string>", "exec")
        exec(compiled_code, globals(), local_vars)

        return plt.gcf()
    
    except Exception as e:
        st.error(f"Error executing code: {e}")
        print(f"Error executing code: {e}")
        return None