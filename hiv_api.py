from api import create_app
from api.cli import icd10, user

app = create_app()
icd10.register(app)
user.register(app)


if __name__ == "__main__":
    app.run()
