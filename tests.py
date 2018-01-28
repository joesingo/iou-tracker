import pytest

from iou import IOUApp, Statement, Transaction
from exceptions import DuplicateUsernameError, InvalidUsernameException

class TestApp(object):
    @pytest.fixture
    def iou_app(self):
        app = IOUApp(db_path=":memory:")
        app.create_tables()
        return app

    def test_user_auth(self, iou_app):
        """
        Test the method that verifies a username and password combination.
        """
        iou_app.add_user("joe", "password123")
        assert not iou_app.authenticate_user("nonexistent", "pass")
        assert not iou_app.authenticate_user("joe", "wrong_password")
        assert iou_app.authenticate_user("joe", "password123")

    def test_duplicate_user(self, iou_app):
        """
        Test that cannot create a user with an already taken username.
        """
        iou_app.add_user("joe", "password123")
        with pytest.raises(DuplicateUsernameError):
            iou_app.add_user("joe", "p")

    def test_totals(self, iou_app):
        """
        Test methods to get total IOU balances and transaction lists.
        """
        iou_app.add_user("john", "pass")
        iou_app.add_user("paul", "pass")
        iou_app.add_user("george", "pass")
        timestamp = 100

        t_john_paul = [
            Transaction("john", "paul", 10, timestamp, "comment"),
            Transaction("john", "paul", 20, timestamp - 1, "comment"),
            Transaction("paul", "john", 5, timestamp - 2, "comment"),
        ]
        t_paul_george = [
            Transaction("paul", "george", 50, timestamp, "comment"),
        ]
        t_john_george = []
        iou_app.add_transactions(t_john_paul + t_paul_george + t_john_george)

        assert list(iou_app.get_ious("john")) == [Statement("john", "paul", -25, 5, 30)]
        expected = set([Statement("paul", "john", 25, 30, 5),
                        Statement("paul", "george", -50, 0, 50)])
        assert set(iou_app.get_ious("paul")) == expected

        t_john_paul = list(iou_app.get_transactions("john", "paul"))
        t_john_george = list(iou_app.get_transactions("john", "george"))
        t_paul_george = list(iou_app.get_transactions("paul", "george"))

        assert list(iou_app.get_transactions("john", "paul")) == t_john_paul
        assert list(iou_app.get_transactions("john", "george")) == t_john_george
        assert list(iou_app.get_transactions("paul", "george")) == t_paul_george

    def test_get_transactions(self, iou_app):
        """
        Test that the method to retrieve transactions is symmetric wrt the
        other the usernames are passed to it
        """
        iou_app.add_user("joe", "pass")
        iou_app.add_user("bob", "pass")

        t_list = [Transaction("joe", "bob", 10, 100, "c"),
                  Transaction("joe", "bob", 11, 90, "c2"),
                  Transaction("bob", "joe", 12, 80, "c3")]

        j_b = list(iou_app.get_transactions("joe", "bob"))
        b_j = list(iou_app.get_transactions("bob", "joe"))
        assert j_b == b_j

    def test_invalid_user(self, iou_app):
        """
        Check that an appropriate exception is raised when trying to add a
        transaction with an invalid username
        """
        iou_app.add_user("joe", "password123")
        with pytest.raises(InvalidUsernameException):
            iou_app.add_transactions([Transaction("joe", "someoneelse", 10, 0, "comment")])
