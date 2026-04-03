# Use Python 3.10
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the ports for FastAPI (8000) and Streamlit (7860)
# Note: Hugging Face default port is 7860
EXPOSE 7860

# Create a shell script to run both
RUN echo "#!/bin/bash\nuvicorn app.main:app --host 0.0.0.0 --port 8000 &\nstreamlit run app/app.py --server.port 7860 --server.address 0.0.0.0" > start.sh
RUN chmod +x start.sh

CMD ["./start.sh"]