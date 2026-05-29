import streamlit as st

# Cấu hình tiêu đề trang
st.set_page_config(page_title="About Me", page_icon="📋")

# Tiêu đề trang
st.title("About Me")

# Thông tin cá nhân
st.header("🧑‍💻 Personal Information")
st.write("""
- **Name:** Thân Trọng Tính  
- **Email:** [thantrongtinh.1912004@gmail.com](mailto:thantrongtinh.1912004@gmail.com)
- **Phone:** 0769420321  
- **Facebook:** [Thân Trọng Tính](https://www.facebook.com/thantrongtinh.1912004)
""")

# Link GitHub
st.header("🔗 GitHub & Repository")
st.write("""
- **GitHub Profile:** [GitHub](https://github.com/Tinhk4)  
""")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
