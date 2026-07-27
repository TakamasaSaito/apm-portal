"""シードスクリプト — seed_master → seed_demands の順に投入する。
main.py から呼ばれる他、単独実行も可能:
  python scripts/seed_master.py && python scripts/seed_demands.py
  python scripts/seed.py  # 両方まとめて実行
"""
import importlib.util
import os


def _load(filename):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def seed():
    _load("seed_master.py").seed_master()
    _load("seed_demands.py").seed_demands()


if __name__ == "__main__":
    seed()
