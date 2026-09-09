import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client = create_client(self.url, self.key)

    def get_client(self):
        return self.client


supabase_client = SupabaseClient().get_client()