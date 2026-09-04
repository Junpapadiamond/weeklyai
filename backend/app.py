from pathlib import Path

# Vercel loads this entrypoint with the module name ``app``. Without a package
# path, that shadows the adjacent ``app/`` package and makes the import below
# resolve back to this file. Teach the entrypoint where its package lives when
# the Vercel loader uses that name; normal local imports keep their usual path.
if __name__ == "app":
    __path__ = [str(Path(__file__).resolve().parent / "app")]
    from app.__init__ import create_app
else:
    from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
