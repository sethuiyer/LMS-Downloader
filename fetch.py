from robobrowser import RoboBrowser
import time
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
    if username == 'myusernamehere' and password == 'mypasswordhere':
        username=raw_input("Enter your LMS username")
        password = raw_input("Enter Password: ")
        with open('credentials/lms.yml','w') as f:
            data = {'user':{'username': username,'password': password}}
            yaml.dump(data,f,default_flow_style=False)
    form['username'].value = username
    form['password'].value = password
    browser.submit_form(form)
    return browser


def fetch_registered_courses(browser):
    ''' Fetch the registered courses from this active session
    '''
    newurl = "http://photon.bits-goa.ac.in/lms/my/"
    time.sleep(2)
    browser.open(newurl)
    coursesreg = []
    p = re.compile(r'\([^)]*\)')
    courseset = set()
    for div in browser.find_all('div', {'class': 'box coursebox'}):
        a = div.findAll('a', href=True)
        for courselink in a:
            courseinfo = {'coursetitle': '', 'url': ''}
            coursetitle = re.sub(p, '', courselink['title']).replace('&amp;amp;', 'AND')
            if coursetitle in courseset:
                continue
            else:
                courseset.add(coursetitle)
            courseurl = courselink['href']
            courseinfo['coursetitle'] = coursetitle
            courseinfo['url'] = courseurl
            coursesreg.append(courseinfo)
    return coursesreg


def write_into_csv(coursesreg):
    ''' Write the list of dictionary in csv
    '''
    courseinfo = {'coursetitle': '', 'url': ''}
    with open('courseinfo.csv', 'wb') as f:
        w = csv.DictWriter(f, courseinfo.keys())
        w.writeheader()
        for coursesdict in coursesreg:
            w.writerow(coursesdict)


def fetch_and_make_json():
    ''' Fetch the list and make json
    '''
    coursewise = []
    print 'Fetching the mateials',
    with open('courseinfo.csv', 'rb') as f:
        coursereader = csv.reader(f, delimiter=',')
        browser = login_to_lms()
        next(coursereader,None)
        for courses in coursereader:
            print '.',
            #print courses[1]
            coursetitlebar = []
            courseurlbar = []  
            browser.open(courses[1])
            print 'Now Parsing the subject ',courses[0]
            # check and parse folders first
            coursetitlebar,courseurlbar = parse_for_folders(browser)
            coursetitlebar2,courseurlbar2 = parse_for_resources(browser)
            for coursetitles in coursetitlebar2:
                coursetitlebar.append(coursetitles)
            for courseurls in courseurlbar2:
                courseurlbar.append(courseurls)
            
            coursewise.append({
                'coursename': courses[0],
                'materialtext': coursetitlebar,
                'materialurl': courseurlbar
                    })
        print ''
        with open('all_materials.json', 'w') as outfile:
            outfile.write(json.dumps(coursewise))
        print 'Everything is Extracted to the JSON file!'

def parse_for_resources(browser):
    coursetitlebar = []
    courseurlbar = []
    for li in browser.find_all('li', {'class': 'activity resource modtype_resource'}):
            a = li.findAll('a', href=True)
            for attachlink in a:
                docutype = str(attachlink.contents[0])[-13:]

                materialtitle=str(attachlink.contents[2])
                materialtitle = re.sub('<[^<]+?>', '', materialtitle)
                materialtitle = materialtitle [: -5]
                if "powerpoint" in docutype:
                    materialtitle = materialtitle + '.pptx'
                elif "document" in docutype:
                    materialtitle = materialtitle + '.docx'
                elif 'pdf' in docutype:
                    materialtitle = materialtitle + '.pdf'
                else:
                    pass
                print 'Document found: ',materialtitle
                coursetitlebar.append(materialtitle)
                if materialtitle[-3:] == 'pdf':
                    browser.open(attachlink['href'])
                    for links in browser.find_all('div', {'class' : 'resourcecontent'}):
                        aa = links.findAll('a', href = True)
                        for kk in aa:
                            print kk['href']
                            courseurlbar.append(kk['href'])
                else:
                    #print attachlink['href']
                    courseurlbar.append(attachlink['href'])
    return coursetitlebar,courseurlbar

def parse_for_folders(browser):
    coursetitlebar=[]
    courseurlbar=[]
    for li in browser.find_all('li', {'class': 'activity folder modtype_folder'}):
        a = li.findAll('a', href=True)
        for attachlink in a:
            materialtitle=str(attachlink.contents[2])
            materialtitle = re.sub('<[^<]+?>', '', materialtitle)
            materialtitle = materialtitle [: -6]
            print 'Folder detected:',materialtitle
            print 'Opening the folder..'
            browser.open(attachlink['href'])
            for div in browser.find_all('span',{'class': 'fp-filename'}):
                for x in div.contents:
                    if str(x).strip() != materialtitle.strip ():
                        print 'Document Found: ',str(x)
                        coursetitlebar.append(str(x))
            for div in browser.find_all('span', {'class': 'fp-filename-icon'}):
                a = div.findAll('a', href=True)
                for attachlinks in a:
                    print attachlinks['href']
                    courseurlbar.append(attachlinks['href'])
        browser.back()
    return coursetitlebar, courseurlbar

if __name__ == '__main__':
    pwd = os.getcwd()
    path = pwd + '/courseinfo.csv'
    if not os.path.exists(path):
        print 'Fetching your registered courses..'
        write_into_csv(fetch_registered_courses(login_to_lms()))
        print 'Fetched!'
    path = pwd + '/all_materials.json'
    if not os.path.exists(path):
        fetch_and_make_json()
    print 'Fetched everything'