#!/usr/bin/env python3
import sys
import os
import time
import traceback
from argparse import ArgumentParser
import imaplib
import email
from email.header import decode_header
import json
import logging
import datetime
import pickle
import subprocess
from typing import Callable, List, Tuple, Dict


v_print:Callable
def set_v_print(verbose: bool) -> None:
    """
    Defines the function v_print.
    It prints if verbose is true, otherwise, it does nothing.
    See: http://stackoverflow.com/questions/5980042
    :param verbose: A bool to determine if v_print will print its args.
    """
    global v_print
    v_print = print if verbose else lambda *a, **k: None


def removesuffix(s: str, suffix:str) -> str:
    """Removes the suffix from s."""
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def maybe_notify(cmd: List[str], user: str, msgs: List[Tuple[str, str]]) -> str:
    """Given a list of (subject, time) tuples, note the newest one
    and then send a notification."""
    newest_time = max([datetime.datetime.strptime(removesuffix(t, ' (UTC)'), '%a, %d %b %Y %H:%M:%S %z') for s, t in msgs])
    notified_fn = __file__.replace('.py', '.pickle')
    out = "OK"
    do_notify = False
    previous_newest = {}
    if os.path.exists(notified_fn):
        with open(notified_fn, 'rb') as f:
            previous_newest = pickle.load(f)
        if user not in previous_newest:
            do_notify = True
        elif newest_time > previous_newest[user]:
            do_notify = True
        else:
            out = f"Skipping. Already notified for email on {newest_time}"
    else:
        do_notify = True
    if do_notify:
        out = run([i.replace('USER', user).replace('TIME', newest_time.strftime('%Y-%m-%d %H:%M')) for i in cmd])
        if len(out) == 0:
            out = f'Sent notification for msg on {newest_time}'
        previous_newest[user] = newest_time
        with open(notified_fn, 'wb') as f:
            pickle.dump(previous_newest, f)
    return out


def run(command_list: List[str]) -> str:
    """Pass in a linux command, get back the stdout."""
    r = subprocess.run(command_list, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, encoding='utf-8')
    logging.debug(f"subprocess.run({command_list}) got {r.returncode}.")
    if r.returncode != 0:
        logging.error(f"subprocess.run({command_list}) failed with code {r.returncode}.")
        return f"Error {r.returncode} trying to run({command_list})"
    return r.stdout


#def main(cmd: List[str], imap: Dict[str, str]) -> None:
def main(account: dict) -> None:
    """ Fetch all the unread mail, and send unread ones to maybe_notify.
    """
    start_time = time.time()

    server = imaplib.IMAP4_SSL(account['mailbox'])
    server.login(account['user'], account['password'])
    server.select()
    status, data = server.search(None, '(UNSEEN)')
    if status != 'OK':
        raise Exception(f'Getting the list of messages resulted in {status}')

    unreads = []
    logging.debug(f"There are {len(data[0].split())} UNSEEN items.")
    for num in data[0].split():  # For each email message...
        status, data = server.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE FROM)])')
        if status != 'OK':
            raise Exception(f'Fetching message {num} resulted in {status}')
        logging.debug(f"Fetched message {num}.")
        msg = email.message_from_bytes(data[0][1])
        subject = msg['Subject']
        logging.debug(f"    Subject: {subject}")
        logging.debug(f"    From: {msg['From']}")
        logging.debug(f"    Date: {msg['Date']}")
        codec = 'utf-8'
        if subject.startswith('=?'):
            subject, codec = decode_header(subject)[0]
        if not isinstance(subject, str):
            subject = subject.decode(codec)

        # Append the subject to a list of items
        unreads.append((subject, msg['Date']))

    # Ensure the new feed is written
    update_status = "OK"
    if len(unreads) > 0:
        update_status = maybe_notify(account['notification'], account['user'], unreads)

    server.close()
    server.logout()
    logging.info(f"{time.time() - start_time:2.0f}s {account['user']} {update_status}")
    v_print(update_status)


if __name__ == '__main__':
    parser = ArgumentParser(description="cronjob to check for email and notify for new messages.")
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    set_v_print(args.verbose)

    with open(__file__.replace('.py', '.json')) as f:
       j = json.load(f)
       logfile = os.path.expanduser(j['logfile'])
       accounts = j['accounts']
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    logging.basicConfig(filename=os.path.join(script_dir, logfile),
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M',
                        level=logging.INFO)
    v_print(f"Log at {os.path.join(script_dir, logfile)}")

    try:
        for account in accounts:
            main(account)
    except Exception as e:
        exceptional_text = "Exception: " + str(e.__class__) + " " + str(e)
        logging.critical(exceptional_text)
        logging.critical(traceback.format_exc())
        print(exceptional_text)
        traceback.print_exc(file=sys.stdout)
