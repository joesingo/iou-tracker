PRAGMA foreign_keys = ON;

CREATE TABLE user (
    username TEXT PRIMARY KEY,
    hash     TEXT
);

CREATE TABLE iou_transaction (
    id        INTEGER PRIMARY KEY,
    borrower  TEXT,
    lender    TEXT,
    amount    FLOAT,
    timestamp INTEGER,
    comment   TEXT,
    balance   FLOAT,

    FOREIGN KEY(borrower) REFERENCES user(username),
    FOREIGN KEY(lender) REFERENCES user(username)
);
