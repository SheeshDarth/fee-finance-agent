FROM python:3.12-slim

WORKDIR /app

COPY agent-runtime-requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent_runner.py firestore_worker.py forecasting.py leakage.py ledger.py llm_drafter.py reconciliation.py reminders.py seed_data.py ./
COPY data ./data
COPY feeops_adk ./feeops_adk

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["adk", "api_server", "feeops_adk", "--host", "0.0.0.0", "--port", "8080", "--no-reload", "--use_local_storage"]
