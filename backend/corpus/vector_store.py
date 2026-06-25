"""
corpus/vector_store.py — Creates and manages the deal corpus Vector Store.

RUN THIS ONCE after installing packages. It:
  1. Creates an OpenAI Vector Store
  2. Uploads all 100 deal records
  3. Saves the Vector Store ID to your .env file automatically

After running once, the ID is saved and you never need to run it again.
"""

import os
import io
import logging
from openai_client import get_client
from corpus.seed_deals import get_all_deals, format_for_vector_store

logger = logging.getLogger(__name__)


def create_vector_store() -> str:
    """
    Creates the Vector Store and uploads all deals.
    Returns the vector_store_id string.
    Takes about 2-3 minutes on first run.
    """
    client = get_client()

    print("Creating PursuitIQ deal corpus in OpenAI Vector Stores...")
    print("This runs ONCE and takes about 2-3 minutes. Please wait.\n")

    # 1. Create the Vector Store
    store = client.vector_stores.create(name="pursuitiq-deal-corpus")
    store_id = store.id
    print(f"Vector Store created: {store_id}")

    # 2. Generate all 100 deals and format as text files
    deals = get_all_deals()
    print(f"Preparing {len(deals)} deal records for upload...")

    file_objects = []
    for deal in deals:
        content  = format_for_vector_store(deal)
        file_obj = io.BytesIO(content.encode("utf-8"))
        file_obj.name = f"{deal['id']}.txt"
        file_objects.append(file_obj)

    # 3. Upload all files in one batch
    print("Uploading to OpenAI...")
    batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=store_id,
        files=file_objects,
    )

    if batch.status != "completed":
        raise RuntimeError(f"Upload failed with status: {batch.status}")

    print(f"Upload complete! {batch.file_counts.completed}/{batch.file_counts.total} files uploaded.")

    # 4. Save the ID to .env so it persists
    _save_id_to_env(store_id)

    print(f"\nVector Store ready!")
    print(f"   ID saved to .env automatically: VECTOR_STORE_ID={store_id}")
    print(f"   You will NOT need to run this again.\n")

    return store_id


def get_or_create() -> str:
    """
    Called at app startup.
    Returns existing Vector Store ID from .env, or creates a new one.
    """
    from config import VECTOR_STORE_ID
    if VECTOR_STORE_ID:
        logger.info(f"Using existing Vector Store: {VECTOR_STORE_ID}")
        return VECTOR_STORE_ID
    logger.info("No Vector Store ID found — creating one now...")
    return create_vector_store()


def _save_id_to_env(store_id: str):
    """Writes VECTOR_STORE_ID=... into the .env file in the current folder."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)

    # Read existing .env content
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Replace or add the VECTOR_STORE_ID line
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("VECTOR_STORE_ID="):
            new_lines.append(f"VECTOR_STORE_ID={store_id}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"VECTOR_STORE_ID={store_id}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)


# ── Run directly: python -m corpus.vector_store ───────────────────────────────
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    create_vector_store()