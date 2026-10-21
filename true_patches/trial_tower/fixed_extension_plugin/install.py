"""Install the Alpha+ extended fixed-room adapter as a standard SkyTemple plugin wheel."""
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

WHEEL = 'alpha_fixed_extension-1.0.0-py3-none-any.whl'
INFO = 'alpha_fixed_extension-1.0.0.dist-info'


def main():
    destination = Path(os.environ['LOCALAPPDATA']) / 'skytemple/plugins'
    destination.mkdir(parents=True, exist_ok=True)
    files = {
        'alpha_fixed_extension/format.py': Path(__file__).resolve().parents[1].joinpath('fixed_extension.py').read_bytes(),
        'alpha_fixed_extension/__init__.py': Path(__file__).with_name('alpha_fixed_extension.py').read_bytes(),
        INFO + '/METADATA': b'Metadata-Version: 2.1\nName: alpha-fixed-extension\nVersion: 1.0.0\nSummary: Alpha+ extended fixed room editing\n',
        INFO + '/WHEEL': b'Wheel-Version: 1.0\nGenerator: Alpha+\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
        INFO + '/entry_points.txt': b'[skytemple.module]\nalpha_fixed_extension = alpha_fixed_extension:AlphaFixedExtensionModule\n',
        INFO + '/top_level.txt': b'alpha_fixed_extension\n',
    }
    rows = io.StringIO(newline='')
    writer = csv.writer(rows)
    for name, blob in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(blob).digest()).rstrip(b'=').decode()
        writer.writerow((name, 'sha256=' + digest, len(blob)))
    writer.writerow((INFO + '/RECORD', '', ''))
    files[INFO + '/RECORD'] = rows.getvalue().encode()
    path = destination / WHEEL
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        for name, blob in files.items():
            archive.writestr(name, blob)
    print(path)


if __name__ == '__main__':
    main()
