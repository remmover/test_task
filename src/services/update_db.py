import os
import csv


from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


from src.database.models import User, Dictionary, Plan, Credit, Payment

excel_folder = "data"
file_extension = "csv"


def get_excel_files(folder):
    excel_files = []
    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
            excel_files.append(os.path.join(folder, filename))
    return excel_files


def import_data_from_excel(file_path, session, table_name):
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        csvFile = csv.DictReader(file, delimiter="\t")
        for row in csvFile:
            match table_name:
                case "dictionary":
                    data_dictionary = Dictionary(
                        name=row["name"],
                    )
                    session.add(data_dictionary)

                case "users":
                    data_user = User(
                        login=row["login"], registration_date=row["registration_date"]
                    )
                    session.add(data_user)

                case "plans":
                    data_plans = Plan(
                        period=row["period"],
                        sum=row["sum"],
                        category_id=row["category_id"],
                    )
                    session.add(data_plans)

                case "credits":
                    data_credits = Credit(
                        user_id=row["user_id"],
                        issuance_date=row["issuance_date"],
                        return_date=row["return_date"],
                        actual_return_date=row["actual_return_date"] or None,
                        body=int(row["body"]),
                        percent=float(row["percent"]),
                    )
                    if data_credits.actual_return_date:
                        data_credits.credit = True
                    session.add(data_credits)

                case "payments":
                    data_payments = Payment(
                        credit_id=row["credit_id"],
                        payment_date=row["payment_date"],
                        type_id=row["type_id"],
                        sum=float(row["sum"]),
                    )
                    session.add(data_payments)
            session.commit()


def main():
    """
    This script imports data from CSV files into a MySQL database using SQLAlchemy. It processes CSV files containing data for different database tables, such as "users," "dictionary," "plans," "credits," and "payments." Each table has a specific structure, and the script maps CSV data to corresponding database table columns.

    The script performs the following steps:
    1. Defines constants for the folder containing CSV files and the file extension.
    2. Provides functions to retrieve a list of CSV files in the specified folder and to import data from a CSV file into the database.
    3. Connects to the MySQL database using SQLAlchemy and session management.
    4. Specifies the order in which tables should be processed.
    5. Iterates through the tables in the specified order, checks if a corresponding CSV file exists, and imports data into the database.
    6. Commits changes to the database after processing each CSV file.

    Note: This script assumes that you have a MySQL database running locally with the specified credentials and that the database tables (User, Dictionary, Plan, Credit, Payment) are defined in the "src.database.models" module.

    Usage:
    - Run this script to import data from CSV files into the MySQL database.

    """
    engine = create_engine("mysql+mysqlconnector://root:456789@localhost:3306/mysql1")#
    Session = sessionmaker(bind=engine)

    excel_files = get_excel_files(excel_folder)

    table_order = ["users", "dictionary", "plans", "credits", "payments"]

    for table_name in table_order:
        excel_file = os.path.join(excel_folder, f"{table_name}.{file_extension}")
        if excel_file in excel_files:
            with Session() as session:
                import_data_from_excel(excel_file, session, table_name)
    print("Success")


if __name__ == "__main__":
    main()
