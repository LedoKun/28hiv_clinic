from hivclinic import create_app
from hivclinic.cli import icd10
from hivclinic.cli import patient_import


app = create_app()
icd10.register(app)
patient_import.register(app)

if __name__ == "__main__":
    app.run()
