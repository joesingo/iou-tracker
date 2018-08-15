import sys
import sqlite3
from collections import namedtuple

from passlib.hash import pbkdf2_sha256

from exceptions import DuplicateUsernameError, InvalidUsernameException


# `owed` is the amount `other_person` owes `user` - may be negative
Statement = namedtuple("Statement", ["user", "other_person", "owed",
                                     "total_owed", "total_borrowed"])


class Transaction:
    def __init__(self, borrower, lender, amount, timestamp, comment,
                 balance=None):
        self.borrower = borrower
        self.lender = lender
        self.amount = amount
        self.timestamp = timestamp
        self.comment = comment
        self.balance = balance

    def to_tuple(self):
        return (self.borrower, self.lender, self.amount, self.timestamp,
                self.comment, self.balance)

    def to_dict(self):
        return {
            "borrower": self.borrower,
            "lender": self.lender,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "comment": self.comment,
            "balance": self.balance
        }

    def __eq__(self, x):
        return self.to_tuple() == x.to_tuple()

    def __repr__(self):
        return repr(self.to_tuple())


class IOUApp:
    def __init__(self, db_path="ioudb"):
        conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        # This gives the ability to access results by key instead of just index
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()

        # Enforce foreign key checking
        conn.execute("PRAGMA foreign_keys = ON;")

    def create_tables(self):
        """
        Read the table definitions in the schema file and execute them. Print
        a warning if the tables have already been created.
        """
        # use iou_transaction as test for whether all tables have been created
        self.cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='iou_transaction'
        """)
        row = self.cursor.fetchone()
        if row is not None:
            sys.stderr.write("warning: tables already exist\n")
            return

        with open("schema.sql") as schema_file:
            self.cursor.executescript(schema_file.read())

    def add_user(self, username, password):
        password_hash = pbkdf2_sha256.encrypt(password, rounds=2000, salt_size=16)
        try:
            self.cursor.execute("INSERT INTO user VALUES (:username, :hash)",
                                {"username": username, "hash": password_hash})
        except sqlite3.IntegrityError:
            raise DuplicateUsernameError("Username '{}' is already taken".format(username))

    def authenticate_user(self, username, password):
        """
        Return True if (username, password) is a valid login, and False
        otherwise.
        """
        self.cursor.execute("SELECT hash FROM user WHERE username=?;", (username,))
        row = self.cursor.fetchone()
        if not row:
            return False

        return pbkdf2_sha256.verify(password, row["hash"])

    def get_transaction_balance(self, transaction):
        """
        Calculate the `balance` field for a new transaction
        """
        # Get the most previous entry for these users
        query = """
            SELECT lender, balance
            FROM iou_transaction
            WHERE (borrower = :user1 AND lender = :user2) OR
                  (borrower = :user2 AND lender = :user1)
            ORDER BY timestamp DESC
            LIMIT 1
        """
        self.cursor.execute(query, {"user1": transaction.lender,
                                    "user2": transaction.borrower})
        row = self.cursor.fetchone()
        if row:
            sign = 1 if row["lender"] == transaction.lender else -1
            prev_balance = row["balance"] * sign
        else:
            print("First transaction!")
            prev_balance = 0

        return transaction.amount + prev_balance

    def add_transactions(self, t_list):
        """
        Store a list of Transaction objects in the database.
        """
        for transaction in t_list:
            transaction.balance = self.get_transaction_balance(transaction)
            try:
                self.cursor.execute(
                    "INSERT INTO iou_transaction VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                    transaction.to_tuple()
                )
            except sqlite3.IntegrityError:
                raise InvalidUsernameException("Invalid username in list of transactions")

    def get_ious(self, user):
        """
        Yield instances of Statement for all IOUs associated with the given user
        """
        query = """
            SELECT
                other_person,
                SUM(amount_owed) AS owed,
                SUM(borrow) AS total_borrowed,
                SUM(lend) AS total_owed
            FROM (
                SELECT
                    (CASE borrower WHEN :user THEN lender ELSE borrower END) AS other_person,
                    amount * (CASE lender WHEN :user THEN 1 ELSE -1 END) AS amount_owed,
                    amount * (CASE lender WHEN :user THEN 1 ELSE 0 END) AS lend,
                    amount * (CASE lender WHEN :user THEN 0 ELSE 1 END) AS borrow
                FROM iou_transaction
                WHERE borrower = :user OR lender = :user
            )
            GROUP BY other_person;
        """
        self.cursor.execute(query, {"user": user})
        for row in self.cursor.fetchall():
            yield Statement(user, row["other_person"], row["owed"],
                            row["total_owed"], row["total_borrowed"])

    def get_transactions(self, user1, user2):
        """
        Yield instances of Transaction for each transaction between user1 and
        user2
        """
        query = """
            SELECT borrower, lender, amount, timestamp, comment, balance
            FROM iou_transaction
            WHERE (borrower = :user1 AND lender = :user2) OR
                  (borrower = :user2 AND lender = :user1)
            ORDER BY timestamp DESC;
        """
        self.cursor.execute(query, {"user1": user1, "user2": user2})
        for row in self.cursor.fetchall():
            yield Transaction(row["borrower"], row["lender"], row["amount"],
                              row["timestamp"], row["comment"], row["balance"])
