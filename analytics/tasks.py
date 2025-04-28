import os
import logging
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

def delete_analytics_reports_in_media():
    media_root = settings.MEDIA_ROOT
    extensions_to_delete = ['.pdf', '.xlsx']

    deleted_files = []

    for root, dirs, files in os.walk(media_root):
        for file in files:
            if any(file.endswith(ext) for ext in extensions_to_delete):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")

    logger.info(f"Deleted {len(deleted_files)} files at midnight.")
