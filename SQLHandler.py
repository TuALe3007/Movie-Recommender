import mysql.connector

# Handles sql database operations
class SQLHandler:

    def __init__(self):
        # Connecting to the local sql database
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Tao0b!et",
            database="sideproject",
            autocommit=True
        )

        self.cursor = self.db.cursor()

        # Printing out all the available users for ease of use
        print("Available Users")
        self.cursor.execute("SELECT * FROM users")
        for x in self.cursor:
            print(x)

        # self.cursor.execute("DROP TABLE users")
        # self.cursor.execute("CREATE TABLE users (" +
        #               "userid INTEGER AUTO_INCREMENT PRIMARY KEY, " +
        #               "username VARCHAR(64) NOT NULL UNIQUE, " +
        #               "password VARCHAR(64) NOT NULL)")

        # cursor.execute("CREATE DATABASE sideproject")
        # cursor.execute("SHOW DATABASES")

        # cursor.execute("DESCRIBE TABLE users")

    # Registering new user
    def registerUser(self, new_user, new_pass):
        if len(str(new_pass)) < 3 or len(str(new_user)) < 2:
            print('Lengths not appropriate')
            return False

        try:
            cursor = self.db.cursor()
            statement = "INSERT INTO users(username, password) VALUES (%s, %s)"
            data = ("'" + new_user + "'", "'" + new_pass + "'")
            cursor.execute(statement, data)
            self.db.commit()
            cursor.close()
            print('Registered')
            return True
        except mysql.connector.Error as e:
            print(e)
            return False

    # Checking provided username or password to see if match
    def authenticateUser(self, username, password):
        try:
            cursor = self.db.cursor()
            statement = "SELECT username FROM users WHERE username=%s AND password=%s"
            data = ("'" + username + "'", "'" + password + "'")
            cursor.execute(statement, data)
            count = 0
            for x in cursor:
                count = count + 1
            self.db.commit()
            cursor.close()
            if count == 0:
                print('Wrong Username or Password')
                return False
            return username
        except mysql.connector.Error as e:
            print(e)
            return False

    # Get the userid from username
    def getUserId(self, username):
        try:
            user = []
            user.append("'" + username + "'")
            cursor = self.db.cursor()
            statement = "SELECT userid FROM users WHERE username=%s"
            data = (user)
            cursor.execute(statement, data)

            count = 0
            for x in cursor:
                count = count + 1
                user_id = x
            self.db.commit()
            cursor.close()

            if count == 0:
                print('Wrong Username or Password')
                return False
            return user_id
        except mysql.connector.Error as e:
            print(e)
            return False

    # Get all usernames
    def getAllUsers(self):
        try:
            users = []
            statement = "SELECT username FROM users"
            cursor = self.db.cursor()
            cursor.execute(statement)
            for x in cursor:
                users.append(str(x[0]).replace("'", ""))
            self.db.commit()
            cursor.close()

            return users
        except mysql.connector.Error as e:
            print(e)
            return False


def main():
    handler = SQLHandler()


if __name__ == "__main__":
    main()
