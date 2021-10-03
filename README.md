[![Code Climate](https://codeclimate.com/github/dblume/email-notifier/badges/gpa.svg)](https://codeclimate.com/github/dblume/email-notifier)
[![Issue Count](https://codeclimate.com/github/dblume/email-notifier/badges/issue_count.svg)](https://codeclimate.com/github/dblume/email-notifier/issues)
[![License](https://img.shields.io/badge/license-MIT_license-blue.svg)](https://raw.githubusercontent.com/dblume/email-notifer/master/LICENSE.txt)
![python3.x](https://img.shields.io/badge/python-3.x-green.svg)

# email-notifier

email-notifier is a script that scans email and sends a notification for unread messages. 
It doesn't reveal any message contents. It should be run as a cronjob.

## What It Does

It scans email accounts and sends a notification (in this example, a text) for 
any unread messages. This is useful for any email accounts that you rarely check.

If there were any unread emails, it'll send a notification possibly like a text like so:

    FROM user@domainwithemail.com
    SUBJ:New email
    MSG:New email for email@yourdomain.com at 2012-10-10 16:20
    From email_notifier.py

The logfile it writes looks something like this:

    2012-10-09 13:00  0s OK
    2012-10-10 13:00  1s Sent notification for msg on 2012-10-09 16:20:30+00:00
    2012-10-11 13:00  0s OK

## Getting Started

1. Rename email\_notifier.json.sample to email\_notifier.json
2. Customize the variables in email\_notifier.json (More on this below.)
3. Set up a cronjob that runs email\_notifier every day.
4. Set up something to maintain the size of its log file.

## Customizing email\_notifier.json

email\_notifier.json looks like this:

    {
       "logfile": "~/logfile.log",
       "accounts":[{
          "mailbox = "mail.yourdomain.com"
          "user = email@yourdomain.com"
          "password = mooltipass",
          "notification":[
             "ssh",
             "user@domainwithemail.com",
             "printf 'New email for USER at TIME\\nFrom email_notifier.py' | mail -s 'New email' 5555550100@txt.phoneco.net"
          ]
       }]
    }

### The "accounts" Section

This section is a list of email accounts the script should check.

**mailbox**: The IMAP address of the email server.  
**user**: The user for the email address. Usually the email address itself.  
**password**: The IMAP password.

#### The "notification" Section

This section is a Linux command for the notification in the form of an array of strings 
suitable for [Python's subprocess.run()](https://docs.python.org/3/library/subprocess.html#subprocess.run).

The keyword USER is replaced with the account's user, and TIME is replaced with the time of the most recent email.

Given the example above, the complete command sends a ssh command to send an email to phoneco to requests it send a text message 

    ssh user@domainwithemail.com printf 'New email for...' | mail -s 'New email' 5555550100@txt.phoneco.net`.

## Maintaining the size of the logfile

To restrict the size of your logfile, you should use the mechanism provided by your operating system. But if you want to roll your own, putting something like the following in a cronjob will work, too.

    find log/ -maxdepth 1 -name \*\.log -type f ! -executable -print0 | \
    xargs -0 -I{} sh -c 'MAX=200; if [ $(wc -l < "{}") -gt $MAX ]; then \
    TMPF=$(mktemp) && tail -$MAX "{}" > $TMPF && chmod --reference="{}" $TMPF && mv $TMPF "{}"; fi'

## Is it any good?

[Yes](https://news.ycombinator.com/item?id=3067434).


## Debugging

Run the command with the ``--verbose`` flag for verbose logging.

## Licence

This software uses the [MIT License](http://opensource.org/licenses/mit-license.php).
