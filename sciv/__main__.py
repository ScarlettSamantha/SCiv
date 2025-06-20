def bootstrap():
    from .game import OpenCiv

    app = OpenCiv(debug=True)

    try:
        app.run()
    except (SystemExit, AssertionError):
        print("Goodbye :-)")


if __name__ == "__main__":
    bootstrap()
