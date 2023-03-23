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
        print('请选择登录方式')
        print('1. 邮箱登录')
        print('2. 手机号+密码登录')
        print('3. 手机号+验证码登录')
        via = input('选择: ')
        if via not in '123':
            print('无效选择')
            return choose()
        return via

    if not save:
        choice = choose()
        if choice == '1':
            email = input('邮箱: ')
            passwd = input('密码: ')
            try:
                apis.login.LoginViaEmail(email, passwd)
            except apis.login.LoginFailedException:
                print('登录失败')
                login()
        elif choice == '2':
            phone = input('手机号: ')
            passwd = input('密码: ')
            try:
                apis.login.LoginViaCellphone(phone, passwd)
            except apis.login.LoginFailedException:
                print('登录失败')
                login()
        elif choice == '3':
            phone = input('手机号: ')
            apis.login.SetSendRegisterVerifcationCodeViaCellphone(phone)
            captcha = input('验证码: ')
            try:
                apis.login.LoginViaCellphone(phone, captcha=captcha)
            except apis.login.LoginFailedException:
                print('登录失败')
                login()
        if input('保存登录信息以便自动登录？ (Y/n) ') == 'Y':
            session = DumpSessionAsString(GetCurrentSession())
            with open('save', 'w') as fp:
                fp.write(session)
    else:
        SetCurrentSession(LoadSessionFromString(save))
