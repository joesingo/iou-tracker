import sqlite3
from collections import namedtuple

from passlib.hash import pbkdf2_sha256

from exceptions import DuplicateUsernameError, InvalidUsernameException


Transaction = namedtuple("Transaction", ["borrower", "lender", "amount",
                                         "timestamp", "comment"])


# `owed` is the amount `other_person` owes `user` - may be negative
Statement = namedtuple("Statement", ["user", "other_person", "owed"])


class IOUApp(object):
    def __init__(self, db_path="ioudb"):
        conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        # This gives the ability to access results by key instead of just index
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()

        # Enforce foreign key checking
        conn.execute("PRAGMA foreign_keys = ON;")

    def create_tables(self):
        """
        Read the table definitions in the schema file and execute them
        """
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

    def add_transactions(self, t_list):
        """
        Store a list of Transaction objects in the database.
        """
        try:
            self.cursor.executemany("""INSERT INTO iou_transaction VALUES
                                       (NULL, ?, ?, ?, ?, ?)""", t_list)
        except sqlite3.IntegrityError:
            raise InvalidUsernameException("Invalid username in list of transactions")

    def get_ious(self, user):
        """
        Yield instances of Statement for all IOUs associated with the given user
        """
        query = """
            SELECT other_person, SUM(amount_owed) as total_owed FROM (
                SELECT
                    (CASE borrower WHEN :user THEN lender ELSE borrower END) as other_person,
                    amount * (CASE lender WHEN :user THEN 1 ELSE -1 END) AS amount_owed
                FROM iou_transaction
                WHERE borrower = :user OR lender = :user
            )
            GROUP BY other_person;
        """
        self.cursor.execute(query, {"user": user})
        for row in self.cursor.fetchall():
            yield Statement(user, row["other_person"], row["total_owed"])

    def get_transactions(self, user1, user2):
        """
        Yield instances of Transaction for each transaction between user1 and
        user2
        """
        query = """
            SELECT borrower, lender, amount, timestamp, comment
            FROM iou_transaction
            WHERE (borrower = :user1 AND lender = :user2) OR
                  (borrower = :user2 AND lender = :user1)
            ORDER BY timestamp DESC;
        """
        self.cursor.execute(query, {"user1": user1, "user2": user2})
        for row in self.cursor.fetchall():
            yield Transaction(row["borrower"], row["lender"], row["amount"],
                              row["timestamp"], row["comment"])
