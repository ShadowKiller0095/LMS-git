import mysql.connector as sq
import re
import os
from datetime import datetime, timedelta
from encrypt import  *
import msvcrt

masterPasswordCheck = b'a1DOnVGLGvq08ZI2MigPQyLVHvFhEM65IXARiCfov+Y=' #Secret

mycon = sq.connect(
    host="localhost",
    user="root",
    password="10107121",
    database="test")
if mycon.is_connected():
    print()
    print("*******Connected*******")
elif mycon.is_connected() == False:
    print("*******Failed*******")

print()
print("***********************************************")
print("\tWelcome to Library Management Programme")
print("***********************************************")
print()

cursor = mycon.cursor()

def setup_database(mycon):
    cursor.execute('''CREATE TABLE IF NOT EXISTS Books (
    book_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    publication_year DATE,
    available_copies INT,
    total_copies INT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password varchar(1000),
    phone_number VARCHAR(20))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT,
    member_id INT,
    borrow_date DATE NOT NULL,
    return_date DATE,
    due_date DATE NOT NULL,
    FOREIGN KEY(book_id) REFERENCES Books(book_id),
    FOREIGN KEY(member_id) REFERENCES Members(member_id))''')
    mycon.commit()
def add_book(mycon, book_id,title, author, isbn, publication_year, available_copies,total_copies):
    query = (f"INSERT INTO Books VALUE({book_id},'{title}','{author}',{isbn},'{publication_year}',{available_copies},{total_copies})")
    cursor.execute(query)
    mycon.commit()


def search_books(mycon, search_term):
    cursor = mycon.cursor()
    query = "SELECT * FROM Books WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s"
    search_term = f"%{search_term}%"
    cursor.execute(query, (search_term, search_term, search_term))
    results = cursor.fetchall()
    cursor.close()
    return results


def add_member(mycon,member_ID, first_name, last_name, email, phone_number, x):
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    phone_regex = r"^\+?\d{10,15}$"
    if not re.match(email_regex, email):
        print("Invalid email format.")
        return
    if not re.match(phone_regex, phone_number):
        print("Invalid phone number.")
        return
    query = "INSERT INTO Members (member_ID,first_name, last_name, email, phone_number, password) VALUES (%s,%s, %s, %s, %s,%s)"
    cursor.execute(query, (member_ID,first_name, last_name, email, phone_number, x))
    mycon.commit()

def borrow_book(mycon, book_id, member_id):
    query = "SELECT available_copies FROM Books WHERE book_id = %s"
    cursor.execute(query, (book_id,))
    available_copies = cursor.fetchone()[0]

    if available_copies > 0:
        borrow_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

        query1 = "INSERT INTO Transactions (book_id, member_id, borrow_date, due_date) VALUES (%s, %s, %s, %s)"
        cursor.execute(query1, (book_id, member_id, borrow_date, due_date))

        query2 = "UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = %s"
        cursor.execute(query2, (book_id,))
        mycon.commit()
        return True
    return False

def backup_database(mycon, backup_file="backup.sql"):
    import os
    os.system(f"mysqldump -u root -p test > {backup_file}")
    print(f"Database backed up to {backup_file}")

def restore_database(mycon, backup_file="backup.sql"):
    import os
    os.system(f"mysql -u root -p test < {backup_file}")
    print(f"Database restored from {backup_file}")

def return_book(mycon, transaction_id, return_date=None):
    if return_date is None:
        return_date = datetime.now().strftime('%Y-%m-%d')

    query = "UPDATE Transactions SET return_date = %s WHERE transaction_id = %s"
    cursor.execute(query, (return_date, transaction_id))

    query2 = "UPDATE Books SET available_copies = available_copies + 1 WHERE book_id = (SELECT book_id FROM Transactions WHERE transaction_id = %s)"
    cursor.execute(query2, (transaction_id,))

    mycon.commit()
    print(f"Transaction ID {transaction_id}: Book returned successfully.")


def generate_overdue_report(mycon):
    query = (f'''SELECT Members.first_name, Members.last_name, Books.title, Transactions.due_date FROM Transactions
            JOIN Members ON Transactions.member_id = Members.member_id
            JOIN Books ON Transactions.book_id = Books.book_id
            WHERE Transactions.return_date IS NULL AND Transactions.due_date < {datetime.now().strftime('%Y-%m-%d')}
            ''')
    cursor.execute(query)
    mycon.commit()
    return cursor.fetchall()


def generate_library_report(mycon):
    try:
        queries = {
            "Most Borrowed Books": '''
            SELECT Books.title, COUNT(*) as borrow_count
            FROM Transactions
            JOIN Books ON Transactions.book_id = Books.book_id
            GROUP BY Books.title
            ORDER BY borrow_count DESC
            LIMIT 5 ''',
            "Active Members": '''
            SELECT Members.first_name, Members.last_name, COUNT(*) as borrow_count
            FROM Transactions
            JOIN Members ON Transactions.member_id = Members.member_id
            GROUP BY Members.member_id
            ORDER BY borrow_count DESC
            LIMIT 5''',
            "Monthly Transactions": '''
            SELECT DATE_FORMAT(borrow_date, '%Y-%m') as month, COUNT(*) as transaction_count
            FROM Transactions
            GROUP BY month
            ORDER BY month DESC '''}

        for report, query in queries.items():
            print(f"\n--- {report} ---")
            cursor.execute(query)
            for row in cursor.fetchall():
                print(row)
    except Exception as e:
        print("Please contact the admin if the below error has occurred ")
        print("Error:", e)

def search_members(mycon, search_term):
    search_term = f"%{search_term}%"
    query = "SELECT * FROM Members WHERE member_id LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR email LIKE %s"
    cursor.execute(query, (search_term,search_term, search_term, search_term))
    members = cursor.fetchall()

    if not members:
        print("No members found.")
    else:
        for member in members:
            print(f"Member ID: {member[0]}, Name: {member[1]} {member[2]}, Email: {member[3]}, Phone: {member[4]}")

def admin_menu():
    while True:
        print("\t***** Menu *****")
        print("1. Create a database (IF NOT created)")
        print("2. Add a book")
        print("3. Add a member")
        print("4.To view all members")
        print("5.View member borrowing history")
        print("6.Update any information of the book")
        print("7.Delete a Book")
        print("8.Delete a Member")
        print("9.View overdue books")
        print("10.Generate overdue report ")
        print("11.Update member information")
        print("12.Search a member")
        print("13.To view all books ")
        print("14.If member forgot its password")
        print("15.Generate library report")
        print("16.Create backup database")
        print("17.Restore database")
        print("18. Exit")
        print()
        try:
            option = int(input("Enter option (1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18): "))
            print()
        except ValueError:
            print("Error: Please enter a valid number.")
            continue

        if option == 1:
            setup_database(mycon)

        elif option == 2:
            book_id = int(input("Enter the ID of the book:"))
            title = input("Enter title of the book: ")
            author = input("Enter the author of the book: ")
            isbn = input("Enter ISBN code: ")
            publication_year = input("Enter the publication year of the book (YYYY/MM/DD): ")
            available_copies = int(input("Enter the number of copies available: "))
            total_copies = int(input("Enter total number of copies:"))
            add_book(mycon, book_id, title, author, isbn, publication_year, available_copies,total_copies)

        elif option == 3:
            member_id = int(input("Enter member ID:"))
            first_name = input("Enter the first name of the member: ")
            last_name = input("Enter the last name of the member: ")
            email = input("Enter the email address of the member: ")
            phone_number = input("Enter the phone number of the member: ")
            password = (input("Enter password:"))

            encrypter = AES256(password)
            encrypted = encrypter.encrypt(password)
            x = encrypted.decode()

            add_member(mycon, member_id,first_name, last_name, email, phone_number, x)

        elif option == 4:
            view_all_members(mycon)

        elif option == 5:
            member_id = int(input("Enter the ID of the member:"))
            view_member_borrowing_history(mycon,member_id)

        elif option == 6:
            book_id = int(input("Enter the ID of the book:"))
            title = input("Enter title of the book: ")
            author = input("Enter the author of the book: ")
            isbn = input("Enter ISBN code: ")
            publication_year = input("Enter the publication year of the book (YYYY/MM/DD): ")
            available_copies = int(input("Enter the number of copies available: "))
            total_copies = int(input("Enter total number of copies:"))
            update_book_info(mycon, book_id, title, author, isbn, publication_year, available_copies, total_copies)

        elif option == 7:
            book_id = int(input("Enter the ID of the book:"))
            delete_book(mycon,book_id)

        elif option == 8:
            member_id = int(input("Enter the ID of the member:"))
            delete_member(mycon,member_id)

        elif option == 9:
            view_overdue_books(mycon)

        elif option == 10:
            generate_overdue_report(mycon)

        elif option == 11:
            member_id = int(input("Enter member ID:"))
            first_name = input("Enter the first name of the member: ")
            last_name = input("Enter the last name of the member: ")
            email = input("Enter the email address of the member: ")
            phone_number = input("Enter the phone number of the member: ")
            update_member_info(mycon, member_id, first_name, last_name, email, phone_number)

        elif option == 12:
            search_term = input("Enter the member ID or name to search:")
            search_members(mycon, search_term)

        elif option == 13:
            view_all_books(mycon)

        elif option == 14:
            member_id = int(input("Enter member ID to change password:"))
            forgot_password(mycon, member_id)
            print("Password has been changed.")

        elif option == 15:
            generate_library_report()

        elif option == 16:
            backup_database()

        elif option == 17:
            restore_database()
        
        elif option == 18:
            print("Exiting admin task")
            break

        else:
            print("Invalid input. Try again.")

def view_overdue_books(mycon):
    query = ('''SELECT Members.first_name, Members.last_name, Books.title, Transactions.due_date 
            FROM Transactions
            JOIN Members ON Transactions.member_id = Members.member_id
            JOIN Books ON Transactions.book_id = Books.book_id
            WHERE Transactions.return_date IS NULL AND Transactions.due_date < %s''')
    cursor.execute(query, (datetime.now().strftime('%Y-%m-%d'),))
    overdue_books = cursor.fetchall()

    if not overdue_books:
        print("No overdue books.")
    else:
        for record in overdue_books:
            print(f"Member: {record[0]} {record[1]}, Book: {record[2]}, Due Date: {record[3]}")

def extend_due_date(mycon, transaction_id, extra_days):
    query = "SELECT due_date FROM Transactions WHERE transaction_id = %s"
    cursor.execute(query, (transaction_id,))
    result = cursor.fetchone()

    if result:
        current_due_date = result[0]
        new_due_date = (current_due_date + timedelta(days=extra_days)).strftime('%Y-%m-%d')
        update_query = "UPDATE Transactions SET due_date = %s WHERE transaction_id = %s"
        cursor.execute(update_query, (new_due_date, transaction_id))
        mycon.commit()
        print(f"Due date extended by {extra_days} days. New due date: {new_due_date}")
    else:
        print(f"Transaction ID {transaction_id} does not exist.")

def delete_member(mycon, member_id):
    q = f"DELETE FROM transactions WHERE member_id ={member_id} ;"
    cursor.execute(q)
    mycon.commit()

    q = "DELETE FROM members WHERE member_id = %s"
    print(f"Executing Query: {q} with parameters: {(member_id,)}")  # Debug print
    cursor.execute(q, (member_id,))
    mycon.commit()
    print("Member deleted successfully.")

def forgot_password(mycon, member_id):
    password = (input("Enter new password:"))
    encrypter = AES256(password)
    encrypted = encrypter.encrypt(password)
    x = encrypted.decode()
    query = "UPDATE members set password = %s where member_id = %s;"
    cursor.execute(query, (x, member_id))
    mycon.commit()

def view_member_borrowing_history(mycon, member_id):
    query = '''
    SELECT Books.title, Transactions.borrow_date, Transactions.due_date, Transactions.return_date
    FROM Transactions
    JOIN Books ON Transactions.book_id = Books.book_id
    WHERE Transactions.member_id = %s
    '''
    cursor.execute(query, (member_id,))
    history = cursor.fetchall()

    if not history:
        print("No borrowing history for this member.")
    else:
        for record in history:
            status = "Returned" if record[3] else "Not Returned"
            print(f"Title: {record[0]}, Borrow Date: {record[1]}, Due Date: {record[2]}, Status: {status}")

def delete_book(mycon, book_id):
    query = "DELETE FROM Books WHERE book_id = %s"
    cursor.execute(query, (book_id,))
    mycon.commit()
    print(f"Book ID {book_id} deleted successfully.")

def update_book_info(mycon, book_id, title=None, author=None, isbn=None, publication_year=None, available_copies=None, total_copies=None):
    updates = []
    params = []

    if title:
        updates.append("title = %s")
        params.append(title)
    if author:
        updates.append("author = %s")
        params.append(author)
    if isbn:
        updates.append("isbn = %s")
        params.append(isbn)
    if publication_year:
        updates.append("publication_year = %s")
        params.append(publication_year)
    if available_copies:
        updates.append("available_copies = %s")
        params.append(available_copies)
    if total_copies:
        updates.append("total_copies = %s")
        params.append(total_copies)

    params.append(book_id)
    query = f"UPDATE Books SET {', '.join(updates)} WHERE book_id = %s"
    cursor.execute(query, tuple(params))
    mycon.commit()
    print(f"Book ID {book_id} updated successfully.")

def update_member_info(mycon, member_id, first_name=None, last_name=None, email=None, phone_number=None):
    updates = []
    params = []

    if first_name:
        updates.append("first_name = %s")
        params.append(first_name)
    if last_name:
        updates.append("last_name = %s")
        params.append(last_name)
    if email:
        updates.append("email = %s")
        params.append(email)
    if phone_number:
        updates.append("phone_number = %s")
        params.append(phone_number)

    params.append(member_id)
    query = f"UPDATE Members SET {', '.join(updates)} WHERE member_id = %s"
    cursor.execute(query, tuple(params))
    mycon.commit()
    print(f"Member ID {member_id} updated successfully.")

def member_login(mycon, member_id, password):

    encrypter = AES256(password)
    encrypted = encrypter.encrypt(password)
    encrypted_password = encrypted.decode()
    cursor = mycon.cursor()

    query = "SELECT member_id, first_name, last_name FROM Members WHERE member_id = %s AND password = %s"
    cursor.execute(query, (member_id, encrypted_password))
    member = cursor.fetchone()

    if not member:
        print("No member found with this member ID and password.")
        return None
    else:
        print(f"\t***** Welcome, {member[1]} {member[2]}! *****")
        member_menu(member_id)
        return member[0]


def view_my_borrowed_books(mycon, member_id):
    query = '''
    SELECT Books.title, Transactions.borrow_date, Transactions.due_date
    FROM Transactions
    JOIN Books ON Transactions.book_id = Books.book_id
    WHERE Transactions.member_id = %s AND Transactions.return_date IS NULL
    '''
    cursor.execute(query, (member_id,))
    borrowed_books = cursor.fetchall()

    if not borrowed_books:
        print("You have no borrowed books.")
    else:
        for book in borrowed_books:
            print(f"Title: {book[0]}, Borrow Date: {book[1]}, Due Date: {book[2]}")

def authenticate_user():
    logged_in = False
    while not logged_in:
        master_password = password_input()

        encrypter = AES256(master_password)
        # Here we should compare a hashed version of the password, not an encrypted text.
        if encrypter.encrypt("textToMatch") != masterPasswordCheck:
            print("Password Incorrect")
            print("*************************")
            break
        else:
            logged_in = True
            print("Successfully logged in!")
            print("*************************")
            print("Welcome admin")
    return logged_in


def view_all_books(mycon):
    query = "SELECT * FROM Books"
    cursor.execute(query)
    books = cursor.fetchall()

    if not books:
        print("No books available in the library.")
    else:
        for book in books:
            print(f'''Book ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, ISBN: {book[3]},
             Year: {book[4]}, Available Copies: {book[5]}/{book[6]}''')

def view_all_members(mycon):
    query = "SELECT * FROM Members"
    cursor.execute(query)
    members = cursor.fetchall()

    if not members:
        print("No members registered.")
    else:
        for member in members:
            print(f"Member ID: {member[0]}, Name: {member[1]} {member[2]}, Email: {member[3]}, Phone: {member[4]}")

def check_book_availability(mycon, book_id):
    query = "SELECT available_copies FROM Books WHERE book_id = %s"
    cursor.execute(query, (book_id,))
    result = cursor.fetchone()

    if result:
        available_copies = result[0]
        if available_copies > 0:
            print(f"Book ID {book_id} is available. Copies left: {available_copies}")
            return True
        else:
            print(f"Book ID {book_id} is currently not available.")
            return False
    else:
        print(f"Book ID {book_id} does not exist.")
        return False

def calculate_fine(mycon, transaction_id, fine_per_day=5):
    try:
        query = "SELECT due_date FROM Transactions WHERE transaction_id = %s"
        cursor.execute(query, (transaction_id,))
        due_date = cursor.fetchone()[0]

        overdue_days = (datetime.now() - datetime.strptime(due_date, '%Y-%m-%d')).days
        if overdue_days > 0:
            fine = overdue_days * fine_per_day
            print(f"Transaction ID {transaction_id} has a fine of ${fine}.")
            return fine
        else:
            print("No fine for this transaction.")
            return 0
    except Exception as e:
        print("Please contact the admin if the below error has occurred ")
        print("Error:",e)

def suggest_books(mycon, member_id):
    try:
        query = '''
        SELECT DISTINCT B2.title
        FROM Transactions T1
        JOIN Books B1 ON T1.book_id = B1.book_id
        JOIN Books B2 ON B1.author = B2.author
        WHERE T1.member_id = %s AND B2.book_id != B1.book_id
        LIMIT 5'''
        cursor.execute(query, (member_id,))
        suggestions = cursor.fetchall()

        if suggestions:
            print("Books you may like:")
            for book in suggestions:
                print(f"- {book[0]}")
        else:
            print("No suggestions available.")
    except Exception as e:
        print("Please contact the admin if the below error has occurred ")
        print("Error:", e)

def view_transaction_history(mycon):
    try:
        query = '''
            SELECT Transactions.transaction_id, Members.first_name, Members.last_name, Books.title, 
            Transactions.borrow_date, Transactions.due_date, Transactions.return_date
            FROM Transactions
            JOIN Members ON Transactions.member_id = Members.member_id
            JOIN Books ON Transactions.book_id = Books.book_id
            ORDER BY Transactions.borrow_date DESC'''
        cursor.execute(query)
        transactions = cursor.fetchall()

        if not transactions:
            print("No transactions available.")
        else:
            for transaction in transactions:
                status = "Returned" if transaction[6] else "Not Returned"
                print(f"Transaction ID: {transaction[0]}, Member: {transaction[1]} {transaction[2]}, "
                    f"Book: {transaction[3]}, Borrow Date: {transaction[4]}, Due Date: {transaction[5]}, "
                    f"Status: {status}")
    except Exception as e:
        print("Please contact the admin if the below error has occurred ")
        print("Error:",e)
def member_menu(member_id):
    while True:
        print("\t\t***** Menu *****")
        print("1.Show all books")
        print("2.Show suggested books")
        print("3.View my borrowed books")
        print("4.Borrow a book")
        print("5.Return a book")
        print("6.Search a book")
        print("7.Extend due date of the book")
        print("8.Check the availability of the book")
        print("9.Fine Calculation")
        print("10.View Transaction History")
        print("11.To change password")
        print("12.Exit")
        print()
        try:
            option = int(input("Enter option (1/2/3/4/5/6/7/8/9/10/11/12): "))
            print()
        except ValueError:
            print("Error: Please enter a valid number.")
            continue
        if option == 1:
            view_all_books(mycon)

        elif option == 2:
            suggest_books(mycon,member_id)

        elif option == 3:
            member_id = int(input("Enter member ID:"))
            view_my_borrowed_books(mycon, member_id)

        elif option == 4:
            book_id = int(input("Enter book ID:"))
            member_id = int(input("Enter member ID:"))
            borrow_book(mycon, book_id, member_id)

        elif option == 5:
            transaction_id = int(input("Enter the transaction ID:"))
            return_book(mycon, transaction_id)

        elif option == 6:
            search_term = input("Enter the name of the book:")
            print(search_books(mycon, search_term))

        elif option == 7:
            transaction_id = int(input("Enter transaction ID:"))
            extra_days = int(input("Enter the number of  extra days required:"))
            extend_due_date(mycon, transaction_id, extra_days)

        elif option == 8:
            book_id = int(input("Enter the ID of the book:"))
            check_book_availability(mycon, book_id)

        elif option == 9:
            transaction_id = int(input("Enter transaction ID:"))
            calculate_fine(mycon, transaction_id, fine_per_day=5)

        elif option == 10:
            view_transaction_history(mycon)

        elif option == 11:
            forgot_password(mycon, member_id)
            print("Password changed")
            print("Please re-login")
            break

        elif option == 11:
            print("Exiting member task")
            break

        else:
            print("Invalid input. Try again.")

import msvcrt

def password_input():
    print("Enter password: ", end="", flush=True)
    password = ""
    while True:
        ch = msvcrt.getch()
        if ch in {b'\r', b'\n'}:  # Enter key pressed
            break
        elif ch == b'\x08':  # Backspace pressed
            if len(password) > 0:
                password = password[:-1]
                print("\b \b", end="", flush=True)  # Erase last *
        else:
            password += ch.decode()
            print("*", end="", flush=True)  # Print * for each char
    print()  # Move to next line after Enter
    return password

while True:
    print("\t***** Menu *****")
    print("1.Admin Login")
    print("2.Member login")
    print("3.Exit")
    print()
    try:
        choice = int(input("Enter choice(1/2/3):"))
        print()
    except ValueError:
        print("Error")
        print("Try again")

    if choice == 1:
        print("\t***** Admin login *****")
        logged_in = authenticate_user()
        if logged_in:
            admin_menu()

    elif choice == 2:
        print("\t***** Member login *****")
        member_id = int(input("Enter the member ID:"))
        password = password_input()  # Call function after definition
        member_login(mycon, member_id, password)        

    elif choice == 3:
        print("Exiting LMS")
        print("Thank You")
        cursor.close()
        break

    else:
        print("Invalid option")
        print("Please try again")