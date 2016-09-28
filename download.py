from robobrowser import RoboBrowser
import re
import csv
import yaml
import os
import json

def login_to_lms():
    ''' Login into lms by using the credentials given in lms.yml'''
    browser = RoboBrowser(parser='html.parser', user_agent='Mozilla')
    login_url = "http://photon.bits-goa.ac.in/lms/login/index.php"
    browser.open(login_url)
    form = browser.get_form(id='login')
    conf = yaml.load(open('credentials/lms.yml'))
    username = conf['user']['username']
    password = conf['user']['password']
    form['username'].value = username
    form['password'].value = password
    browser.submit_form(form)
    return browser


def make_folders():
    ''' Helper function for fetch_materials() '''
    pwd=os.getcwd()
    with open('courseinfo.csv','rb') as f:
        coursereader=csv.reader(f, delimiter=',')
        next(coursereader)
        for row in coursereader:
            folname = row[0].title()
            path = os.path.join(pwd,"Course Materials", folname)
            try: 
                os.makedirs(path)
            except OSError:
                if not os.path.isdir(path):
                    raise


def fetch_materials():
    ''' Fetch the materials from the LMS '''
    pwd = os.getcwd()
    with open('all_materials.json') as f:
        data = json.loads(f.read())
    browser = login_to_lms()
    for dict in data:
        try:
            path = os.path.join(pwd ,"Course Materials",dict['coursename'].title())
            os.chdir(path)
        except OSError:
            make_folders()
        for i in range(len(dict['materialurl'])):
            url = dict['materialurl'][i]
            d = dict['materialtext'][i]
            if '.' not in d:
                browser.open(dict['materialurl'][i])
                for div in browser.find_all('div', {'class': 'resourcecontent'}):
                    a = div.findAll('a', href=True)
                    for attachlink in a:
                        url = attachlink['href']
                print url
                request = browser.session.get(url, stream=True)
                if dict['materialtext'][i][-4] == '.':
                    fname = dict['materialtext'][i]
                else:
                    fname = dict['materialtext'][i] + '.pdf'
                file_path = os.path.join(path,fname)
                print fname + ' is Downloaded'
                with open(file_path, "w") as file:
                    file.write(request.content)
                    continue
            else:
                url = dict['materialurl'][i]
                request = browser.session.get(url, stream=True)
                d = request.headers.get('content-disposition')
                try:
                    fname = str(re.findall("filename=(.+)",d)[0]).replace("\"", "")
                except:

                    fname = dict['materialtext'][i]
                    if '.' not in fname:
                        fname = fname + '.pdf'
                file_path = os.path.join(path,fname)
                print fname + ' is Downloaded'
                with open(file_path, "wb") as file:
                    file.write(request.content)
fetch_materials()
