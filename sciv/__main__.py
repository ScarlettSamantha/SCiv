def bootstrap():
    from .game import SCIV

    app = SCIV(debug=True)

    try:
        app.run()
    except (SystemExit, AssertionError):
        print("Goodbye :-)")


if __name__ == "__main__":
    bootstrap()
