from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI(title="Fraud Feedback Service")

# Setup connection to Supabase/PostgreSQL
# In production, these should be env variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

class FraudLabel(BaseModel):
    transaction_id: str
    is_fraud: bool
    label_source: str # 'chargeback', 'human_review', 'automated'
    labeled_by: str
    notes: str = ""

def write_label_to_db(label: FraudLabel):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        
        insert_query = """
            INSERT INTO fraud_labels 
            (transaction_id, is_fraud, label_source, labeled_by, notes) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(insert_query, (
            label.transaction_id, 
            label.is_fraud, 
            label.label_source, 
            label.labeled_by, 
            label.notes
        ))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error writing to DB: {e}")

@app.post("/v1/feedback/label")
async def submit_label(label: FraudLabel, background_tasks: BackgroundTasks):
    """
    Accepts feedback from case management or automated chargeback systems
    and writes it to the database asynchronously.
    """
    background_tasks.add_task(write_label_to_db, label)
    return {"status": "success", "message": "Label accepted for processing"}

@app.post("/v1/feedback/chargeback")
async def process_chargeback(transaction_id: str, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for payment processor to notify of chargebacks (guaranteed fraud).
    """
    label = FraudLabel(
        transaction_id=transaction_id,
        is_fraud=True,
        label_source="chargeback",
        labeled_by="payment_processor",
        notes="Automated chargeback received"
    )
    background_tasks.add_task(write_label_to_db, label)
    return {"status": "success", "message": "Chargeback registered"}
