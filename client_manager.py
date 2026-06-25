"""
Client file manager.
Handles creating client folders, saving uploaded files, and listing client data.
"""
import os
import re
import shutil
from datetime import datetime

# Root folder that stores one sub-folder per client
CLIENTS_ROOT = os.path.join(os.path.dirname(__file__), 'cliente_files')
os.makedirs(CLIENTS_ROOT, exist_ok=True)

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json'}


def _safe_name(name: str) -> str:
    """Convert a free-text client name to a safe folder/file slug."""
    name = name.strip()
    # Replace spaces and special chars with underscores
    name = re.sub(r'[^\w\-.]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    return name.strip('_')


def list_clients() -> list[dict]:
    """Return a list of existing clients with metadata."""
    clients = []
    for entry in sorted(os.scandir(CLIENTS_ROOT), key=lambda e: e.name):
        if entry.is_dir():
            files = _list_client_files(entry.name)
            clients.append({
                'name': entry.name,
                'display_name': entry.name.replace('_', ' '),
                'file_count': len(files),
                'files': files,
                'created_at': datetime.fromtimestamp(entry.stat().st_ctime).strftime('%Y-%m-%d %H:%M'),
            })
    return clients


def create_client(client_name: str) -> dict:
    """
    Create a new client folder.
    Returns {'ok': True, 'slug': ...} or {'ok': False, 'error': ...}.
    """
    slug = _safe_name(client_name)
    if not slug:
        return {'ok': False, 'error': 'Invalid client name.'}
    path = os.path.join(CLIENTS_ROOT, slug)
    if os.path.exists(path):
        return {'ok': False, 'error': f'Client "{slug}" already exists.'}
    os.makedirs(path, exist_ok=True)
    return {'ok': True, 'slug': slug}


def client_exists(client_slug: str) -> bool:
    return os.path.isdir(os.path.join(CLIENTS_ROOT, _safe_name(client_slug)))


def save_client_file(client_slug: str, file_storage, original_filename: str) -> dict:
    """
    Save an uploaded file to the client's folder.
    Returns {'ok': True, 'path': ..., 'filename': ...} or {'ok': False, 'error': ...}.
    """
    slug = _safe_name(client_slug)
    client_dir = os.path.join(CLIENTS_ROOT, slug)
    if not os.path.isdir(client_dir):
        return {'ok': False, 'error': f'Client "{slug}" does not exist.'}

    # Validate extension
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {'ok': False, 'error': f'File type "{ext}" not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}

    # Build filename: ClientName_originalname_timestamp.ext
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_orig = _safe_name(os.path.splitext(original_filename)[0])
    filename = f"{slug}_{safe_orig}_{ts}{ext}"
    save_path = os.path.join(client_dir, filename)

    file_storage.save(save_path)
    return {'ok': True, 'path': save_path, 'filename': filename}


def _list_client_files(client_slug: str) -> list[dict]:
    """Return file metadata for all files in a client folder."""
    client_dir = os.path.join(CLIENTS_ROOT, _safe_name(client_slug))
    if not os.path.isdir(client_dir):
        return []
    files = []
    for entry in sorted(os.scandir(client_dir), key=lambda e: e.stat().st_mtime, reverse=True):
        if entry.is_file():
            stat = entry.stat()
            files.append({
                'filename': entry.name,
                'size_kb': round(stat.st_size / 1024, 1),
                'uploaded_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'ext': os.path.splitext(entry.name)[1].lower(),
            })
    return files


def get_client_files(client_slug: str) -> list[dict]:
    return _list_client_files(client_slug)


def get_client_file_path(client_slug: str, filename: str) -> str | None:
    """Return absolute path to a client file, or None if it doesn't exist."""
    slug = _safe_name(client_slug)
    # Prevent path traversal
    safe_filename = os.path.basename(filename)
    path = os.path.join(CLIENTS_ROOT, slug, safe_filename)
    if os.path.isfile(path):
        return path
    return None


def delete_client_file(client_slug: str, filename: str) -> dict:
    """Delete a specific file from a client folder."""
    path = get_client_file_path(client_slug, filename)
    if not path:
        return {'ok': False, 'error': 'File not found.'}
    os.remove(path)
    return {'ok': True}


def delete_client(client_slug: str) -> dict:
    """Delete a client folder and all its files."""
    slug = _safe_name(client_slug)
    client_dir = os.path.join(CLIENTS_ROOT, slug)
    if not os.path.isdir(client_dir):
        return {'ok': False, 'error': 'Client not found.'}
    shutil.rmtree(client_dir)
    return {'ok': True}
