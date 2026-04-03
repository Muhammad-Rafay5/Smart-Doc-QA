FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose ports for both services
EXPOSE 8000
EXPOSE 7860

# Start both FastAPI and Streamlit at the same time
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 & sleep 5 && streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0