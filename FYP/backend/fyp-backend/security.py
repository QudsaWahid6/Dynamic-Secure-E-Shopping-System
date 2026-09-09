import hashlib
import json
import datetime
from services.supabase_service import supabase_client

def generate_hash(event_type, event_data, timestamp, previous_hash):
    """SHA-256 hash generate karta hai"""
    data_string = f"{event_type}{json.dumps(event_data, sort_keys=True)}{timestamp}{previous_hash}"
    return hashlib.sha256(data_string.encode()).hexdigest()

def get_last_hash():
    """Database se last hash laata hai"""
    try:
        result = supabase_client.table("security_logs")\
            .select("current_hash")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        if result.data:
            return result.data[0]["current_hash"]
        return "0" * 64  # pehli entry ke liye
    except:
        return "0" * 64

def create_security_record(event_type, event_data, user_id=None, ip_address=None):
    """Naya security log record banata hai"""
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        previous_hash = get_last_hash()
        current_hash = generate_hash(event_type, event_data, timestamp, previous_hash)

        supabase_client.table("security_logs").insert({
            "event_type": event_type,
            "event_data": event_data,
            "user_id": user_id,
            "ip_address": ip_address,
            "current_hash": current_hash,
            "previous_hash": previous_hash,
            "created_at": timestamp
        }).execute()

        return current_hash
    except Exception as e:
        print(f"Security log error: {e}")
        return None

def verify_record(log):
    """Single record verify karta hai"""
    expected_hash = generate_hash(
        log["event_type"],
        log["event_data"],
        log["created_at"],
        log["previous_hash"]
    )
    return expected_hash == log["current_hash"]

def verify_chain():
    """Poori chain verify karta hai"""
    try:
        result = supabase_client.table("security_logs")\
            .select("*")\
            .order("created_at", desc=False)\
            .execute()

        logs = result.data
        if not logs:
            return True, "Chain empty hai"

        for i, log in enumerate(logs):
            if not verify_record(log):
                return False, f"Record {i+1} tampered hai!"

            if i > 0:
                if log["previous_hash"] != logs[i-1]["current_hash"]:
                    return False, f"Chain break at record {i+1}!"

        return True, "Chain valid hai"
    except Exception as e:
        return False, str(e)

def clear_all_logs():
    """Saare security logs delete karta hai (admin only)"""
    try:
        supabase_client.table("security_logs")\
            .delete()\
            .neq("id", "00000000-0000-0000-0000-000000000000")\
            .execute()
        return True, "All logs cleared"
    except Exception as e:
        return False, str(e)