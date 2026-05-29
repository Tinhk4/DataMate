# Sử dụng hình ảnh Streamlit chính thức
FROM python:3.9-slim

# Cài đặt các thư viện cần thiết
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Tạo thư mục ứng dụng
WORKDIR /DataMate

# Sao chép file ứng dụng và yêu cầu vào container Docker, ở thư mục DataMate
COPY . /DataMate
RUN pip install --no-cache-dir -r requirements.txt

# Chạy ứng dụng Streamlit
EXPOSE 8501
CMD ["streamlit", "run", "1_📊_Chat_With_Your_Data.py", "--server.port=8501", "--server.enableCORS=false"]
