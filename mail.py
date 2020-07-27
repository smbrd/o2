import base64
import imaplib
import re
from email.parser import HeaderParser

IMAP_HOST = 'poczta.o2.pl'
IMAP_USER = 'smbrd@o2.pl'
IMAP_PASS = 'Skarb+o2'

EXCLUDE_EMAILS = ['no-response@o2.pl', 'o2@o2.pl']
INCLUDED_FOLDERS = ['INBOX', 'Segregator/Oferty']


def decode_word(word):
    m = re.search(r'=\?(.+)\?(.+)\?(.+)\?=', word)

    if m:
        charset = m.group(1)
        encoding = m.group(2)
        text = m.group(3)

        if encoding != 'B':
            print(f'Unexpected encoding: "{encoding}" in {word}')
            return ''

        return base64.b64decode(text).decode(charset)

    return word


def get_email(from_):
    email = ''

    m = re.search(r'"(.+)" <(.+)>', from_)
    if m:
        email = m.group(2)
    else:
        m = re.search(r'.+ <(.+)>', from_)
        if m:
            email = m.group(1)

    return email


def main():
    mailparser = HeaderParser()

    imap = imaplib.IMAP4_SSL(host=IMAP_HOST, port=993)
    imap.login(IMAP_USER, IMAP_PASS)

    # names = [folder_name.decode('utf-8').split(' "/" ')[1] for folder_name in imap.list()[1]]
    for folder_name in INCLUDED_FOLDERS:
        imap.select(folder_name)

        tmp, messages = imap.search(None, 'ALL')
        # tmp, messages = imap.search(None, '(FROM "o2@o2.pl")')

        for message_id in reversed(messages[0].split()):
            tmp, data = imap.fetch(message_id, '(BODY.PEEK[HEADER])')
            msg = mailparser.parsestr(str(data[0][1].decode('utf-8')))
            email = get_email(msg['From'])

            if email in EXCLUDE_EMAILS:
                print(f'DELETED: {decode_word(msg["Subject"])}')
                ret = imap.store(message_id, '+FLAGS', '\\Deleted')
                if ret[0] != 'OK':
                    print(ret)
    imap.close()
    imap.logout()


if __name__ == '__main__':
    main()
