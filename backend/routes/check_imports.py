import sys

def try_import(name, alias=None):
    try:
        mod = __import__(name)
        print(f"{name} import OK: {getattr(mod, '__version__', 'no-version')}")
    except Exception as e:
        print(f"{name} import ERROR: {e!r}")

if __name__ == '__main__':
    try_import('mysql.connector')
    try_import('google.generativeai')
    try_import('requests')
