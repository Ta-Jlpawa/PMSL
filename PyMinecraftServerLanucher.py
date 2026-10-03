"""PMSL 程序入口；导入时不加载界面或读写配置。"""


def main():
    import sys
    from pathlib import Path

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    from pmsl.bootstrap import main as application_main

    return application_main()


if __name__ == "__main__":
    raise SystemExit(main())
