# Use Python 3.11 to satisfy NetworkX 3.6.1 requirements
FROM python:3.11

# Set the working directory inside the container
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files from your local folder into the container
COPY . .

# Grant full permissions to the code directory for the container user
RUN chmod -R 777 /code

# Tell Hugging Face to listen on port 7860
EXPOSE 7860

# Start both servers:
# 1. FastAPI (Backend) on port 8000
# 2. Streamlit (Frontend) on port 7860
CMD sh -c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 & python -m streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0"