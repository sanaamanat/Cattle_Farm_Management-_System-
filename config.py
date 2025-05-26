class Config:
    SECRET_KEY = 'your_secret_key'  # Replace with a strong secret key

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://DESKTOP-0BOKRG9\\SQLEXPRESS/cattle_farm"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&trusted_connection=yes"
        "&Encrypt=no"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
