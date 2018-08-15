#!/usr/bin/env python3
import sys
import time

from iou import IOUApp, Transaction

def usage(exit_status):
    print("""Usage: setup.py [--tables] [--add-iou <user1> <user2>]

  --tables   Create tables required for app
  --add-iou  Create a blank IOU between two users""")
    sys.exit(exit_status)

if __name__ == "__main__":
    app = IOUApp()

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("-h", "--help"):
            usage(0)
        if arg == "--tables":
            app.create_tables()
            sys.exit(0)
        if arg == "--add-iou":
            try:
                u1 = args[i + 1]
                u2 = args[i + 2]
            except IndexError:
                usage(1)

            ts = int(time.time())
            comment = "Creating IOU for {} and {}".format(u1, u2)
            print(comment)
            app.add_transactions([Transaction(borrower=u1, lender=u2, amount=0,
                                              timestamp=ts, comment=comment,
                                              balance=0)])
            break
    else:
        usage(1)
