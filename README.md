# Backend Server for HIV Clinic WebUI at 28th Public Health Center

## Requirements
* The backend server requires the following dependencies:
    * python (3.6 or newer)
    * python3-pip
    * PostgreSQL (with uuid-ossp module, see https://stackoverflow.com/a/12505220)

* If you need to import patients' information from HCIS system, you will need a Windows PC/VM with the following dependencies:
    * selenium-server
    * IEDriverServer (x86 -- as the x64 driver was not stable)

Please see https://github.com/SeleniumHQ/selenium/wiki/InternetExplorerDriver for the information on how to config the IEDriverServer. 

## Project setup
```
# Rename example.env to .env and edit the file
cp example.env .env
nano .env

# Setup python virtual environment
python3 -m ./venv
source ./venv/bin/activate
pip install -r requirements.txt

# Setup database tables
flask db migrate
flask db upgrate

# Seed ICD10 data to the database
flask icd10 init
```

## Import patient's information from HCIS
```
# Run scraping script
python ./selenium-patient-importer.py

# Imported scraped data to the database
flask patient importjson ./all_patient_info.json
```
Note: Please edit server ip, username and password in the script.


## Run server with hot-reloads for development
```
flask run
```
The backend (dev) server will be avalible at http://localhost:5050


## Lint files
```
black --line-length=79 ./
```

## Todo
* Report generation
* Allow editing/adding patient's information
* User & credential system (Using JWT token)
* Ajax form validation backend
