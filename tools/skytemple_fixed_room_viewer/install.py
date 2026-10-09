"""Build and install a pure-Python wheel through SkyTemple's plugin mechanism."""
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
import zipfile

SOURCE = Path(__file__).resolve().parent
WHEEL = 'alpha_fixed_room_viewer-1.0.0-py3-none-any.whl'
INFO = 'alpha_fixed_room_viewer-1.0.0.dist-info'


def main():
    destination = Path(os.environ['LOCALAPPDATA']) / 'skytemple/plugins'
    destination.mkdir(parents=True, exist_ok=True)
    files = {
        'alpha_fixed_room_viewer/__init__.py': (SOURCE / 'alpha_fixed_room_viewer.py').read_bytes(),
        INFO + '/METADATA': b'Metadata-Version: 2.1\nName: alpha-fixed-room-viewer\nVersion: 1.0.0\nSummary: Read-only Alpha+ expanded fixed-room stats viewer\n',
        INFO + '/WHEEL': b'Wheel-Version: 1.0\nGenerator: Alpha+\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        INFO + '/entry_points.txt': b'[skytemple.module]\nalpha_fixed_room_viewer = alpha_fixed_room_viewer:AlphaFixedRoomViewerModule\n',
        INFO + '/top_level.txt': b'alpha_fixed_room_viewer\n',
    }
    record = io.StringIO(newline='')
    writer = csv.writer(record)
    for name, blob in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(blob).digest()).rstrip(b'=').decode()
        writer.writerow((name, 'sha256=' + digest, str(len(blob))))
    writer.writerow((INFO + '/RECORD', '', ''))
    files[INFO + '/RECORD'] = record.getvalue().encode()
    path = destination / WHEEL
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as wheel:
        for name, blob in files.items():
            wheel.writestr(name, blob)
    print(path)


if __name__ == '__main__':
    main()
