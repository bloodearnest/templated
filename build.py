import sys
import zipfile
import pathlib
import stat


def create_archive(
        source, target, interpreter, compression=zipfile.ZIP_DEFLATED):
    root = pathlib.Path(source)
    dest = pathlib.Path(target)
    with open(target, 'wb') as fd:
        fd.write(
            b'#!' + interpreter.encode(sys.getfilesystemencoding()) + b'\n'
        )
        with zipfile.ZipFile(fd, 'w', compression=compression) as z:
            for child in root.rglob('*'):
                arcname = str(child.relative_to(root))
                z.write(str(child), arcname)

    dest.chmod(dest.stat().st_mode | stat.S_IEXEC)


if __name__ == '__main__':
    create_archive('build', 'reify', '/usr/bin/env python3')
    create_archive(
        'build',
        'reify.uncompressed',
        '/usr/bin/env python3',
        zipfile.ZIP_STORED
    )
