import sys
from pathlib import Path
from pyncm import apis
from pyncm import DumpSessionAsString, SetCurrentSession, LoadSessionFromString, GetCurrentSession


if getattr(sys, "frozen", False):
    datadir = Path(sys.executable).parent
else:
    datadir = Path(__file__).parent
save_path = datadir.joinpath('save')
if not save_path.exists():
    with open(save_path, 'w') as save_fp:
        pass


def login():
    with open(save_path) as fp:
        save = fp.read()

    def choose():
        print('Please choose')
        print('1. Login via email')
        print('2. Login via cellphone')
        via = input('Choice: ')
        if via not in '12':
            print('Invalid choice')
            return choose()
        return via

    if not save:
        choice = choose()
        if choice == '1':
            email, phone = input('Email: '), ''
            passwd = input('Password: ')
            try:
                apis.login.LoginViaEmail(email, passwd)
            except apis.login.LoginFailedException:
                print('Login failed')
                login()
        else:
            phone, email = input('Phone: '), ''
            passwd = input('Password: ')
            try:
                apis.login.LoginViaCellphone(phone, passwd)
            except apis.login.LoginFailedException:
                print('Login failed')
                login()
        if input('Save current session for automatic login? (Y/n) ') == 'Y':
            session = DumpSessionAsString(GetCurrentSession())
            with open('save', 'w') as fp:
                fp.write(session)
    else:
        SetCurrentSession(LoadSessionFromString(save))
