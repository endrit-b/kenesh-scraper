# -*- coding: utf-8 -*-
from pymongo import MongoClient
import mechanize
from BeautifulSoup import BeautifulSoup
import re
import urllib
import os
#import PIL
#from PIL import Image
from unidecode import unidecode
from datetime import datetime

client = MongoClient()
db = client.keneshtest

def scraper():

    # execute absence data scraper.
    scrape_absence_data()

    # execute MP's bio data scraper.
    scrape_mp_bio_data()

    # Download bio images and render thumbnails.
    #download_bio_images()


# Funtction whic will scrape MP's absence data
def scrape_absence_data():

    db.absence.remove({})
    print "\nScraping parliament session absentee data..."

    # load kenesh page
    br = mechanize.Browser()
    br.set_handle_robots(False)  # ignore robots
    br.set_handle_refresh(False)  # can sometimes hang without this
    br.addheaders = [('User-agent', 'Firefox')]  # User-Agent

    # browsing links of previously loaded page
    br1 = mechanize.Browser()
    br1.set_handle_robots(False)  # ignore robots
    br1.set_handle_refresh(False)  # can sometimes hang without this
    br1.addheaders = [('User-agent', 'Firefox')]  # User-Agent

    url = "http://www.kenesh.kg/RU/Folders/4258-Uchastie_deputatov_v_zasedaniyax_ZHogorku_Kenesha.aspx"
    br.open(url)

    absence_count = 1
    for session_idx, link in enumerate(br.links(text_regex="Сведения об участии депутатов в заседаниях")):
        link_url = http://kenesh.kg/RU/Articles/10125-Svedeniya_ob_uchastii_deputatov_v_zasedaniyax_ZHK_0506_sentyabrya_2012_goda.aspx

        print ''
        print 'SESSION: %s' % link_url

        # Open absentees link
        respose = br1.open(link_url)
        # Read content of the link and load it in soup
        html_content = respose.read()
        soup = BeautifulSoup(html_content)

        # Scrape the table from the website
        if soup.find('table', style=lambda x: x and x.startswith('width:102.84')):
            table = soup.find('table', style=lambda x: x and x.startswith('width:102.84'))

        elif soup.find('table', style=lambda x: x and x.startswith('border-bottom: medium none; border-left')):
            table = soup.find('table', style=lambda x: x and x.startswith('border-bottom: medium none; border-left'))

        table_soup = table
        table_rows = table_soup.findAll('tr')

        # Let's create temporary json document
        temp_data = {
            'reason': {
                'counter': 0,
                'value': ''
            },
            'reasonDetail': '',
            'date': {
                'counter': 0,
                'value': ''
            }
        }

        # Iterate through out table rows, use slicing to skip the header
        for absentee_idx, row in enumerate(table_rows[1:]):
            json_obj = {}
            # iterate through every cell in table
            for index, cell in enumerate(row.findAll('td')):
                if index > 0:
                    # Build Json document that we want to save to MongoDB
                    build_absentees_json_obj(row, cell, index, temp_data, json_obj)

            # Let's be sure we include a reference to the data source:
            json_obj['source'] = link_url

            # Time to save the json document in mongodb
            db.absence.insert(json_obj)

            if 'firstName' in json_obj:
                print "%i: %s %s" % (absence_count, json_obj['lastName'], json_obj['firstName'])
            else:
                print "%i: %s" % (absence_count, json_obj['lastName'])

            absence_count = absence_count + 1

            # Decrement counters as the rows iterate
            if temp_data['reason']['counter'] > 0:
                temp_data['reason']['counter'] -= 1
            if temp_data['date']['counter'] > 0:
                temp_data['date']['counter'] -= 1

    print "\nScraping complete"


# Funtction which will scrape MP's bio data
def scrape_mp_bio_data():

    db.deputies.remove({})
    print "\nScraping members of parliament bio..."

    # browsing links in mp's page
    br2 = mechanize.Browser()
    br2.set_handle_robots(False)  # ignore robots
    br2.set_handle_refresh(False)  # can sometimes hang without this
    br2.addheaders = [('User-agent', 'Firefox')]  # User-Agent

    # browsing links for mp's profile page
    br3 = mechanize.Browser()
    br3.set_handle_robots(False)  # ignore robots
    br3.set_handle_refresh(False)  # can sometimes hang without this
    br3.addheaders = [('User-agent', 'Firefox')]  # User-Agent

    deputy_url = "http://www.kenesh.kg/RU/Folders/235-Deputaty.aspx"
    br2.open(deputy_url)

    mp_count = 1

    party_types = ['Фракция', 'депутатская группа', 'АБДЫРАХМАНОВ Омурбек', 'ЖЭЭНБЕКОВ Равшан Бабырбекович']

    # for every party type scrape links data
    # Iterate through out the links of factions and deputies group
    for tp in party_types:
        print " "
        print "Importng data for party type:" + tp
        scrape_mp_link_data(tp, br2, br3, mp_count)

    print "\nScraping complete!"


def build_absentees_json_obj(row, cell, index, temp_data, json_obj):

    if cell.findAll('div'):

        if len(row.findAll('td')) >= 5:
            # Get data from td and if there is rowspan save data
            # temporarly in json document: temp_data
            fill_temp_doc_with_data(cell, index, temp_data)

        # if we are in first cell (first column)
        if index == 1:
            names = cell.findAll('div')
            if len(names) > 1:
                json_obj['firstName'] = re.sub(r' +', ' ', names[1].text).replace('&nbsp;', '').replace('(', '').replace(')', '')
            else:
                json_obj['firstName'] = ""

            json_obj['lastName'] = names[0].text.replace('&nbsp;', '').replace('(', '').replace(')', '')

        # if we are in second cell (second column)
        elif index == 2:
            # if row length is lower than 5,
            # td with index 2 would be column transsferred vote
            if len(row.findAll('td')) < 4:
                json_obj['transferredVoteTo'] = {}
                transferred_vote_to = cell.findAll('div')
                json_obj['transferredVoteTo'] = transferred_vote_to[0].text
                # lets fill json doc with the data from temporary jason
                json_obj['reason'] = temp_data['reason']['value']
                json_obj['reasonDetail'] = temp_data['reasonDetail']
                json_obj['sessionDate'] = temp_data['date']['value']

                absent_days = get_absent_days(temp_data['date']['value'])
                json_obj['absentDaysCount'] = len(absent_days)
                json_obj['absentDays'] = absent_days

            elif len(row.findAll('td')) == 4:
                json_obj['reason'] = temp_data['reason']['value']
                json_obj['reasonDetail'] = temp_data['reasonDetail']

                json_obj['sessionDate'] = {}
                date = cell.findAll('div')
                json_obj['sessionDate'] = date[0].text

                absent_days = get_absent_days(json_obj['sessionDate'])
                json_obj['absentDaysCount'] = len(absent_days)
                json_obj['absentDays'] = absent_days
            else:
                json_obj['reason'] = {}
                reasons = cell.findAll('div')
                json_obj['reason'] = reasons[0].text

                if len(reasons) > 1:
                    json_obj['reasonDetail'] = reasons[1].text.replace('&nbsp;', '').replace('(', '').replace(')', '')

        # if we are in third cell (third column)
        elif index == 3:
            if len(row.findAll('td')) == 4:
                json_obj['transferredVoteTo'] = {}
                transferred_vote_to = cell.findAll('div')
                json_obj['transferredVoteTo'] = transferred_vote_to[0].text

            elif len(row.findAll('td')) > 4:
                json_obj['sessionDate'] = {}
                date = cell.findAll('div')
                json_obj['sessionDate'] = date[0].text

                absent_days = get_absent_days(date[0].text)
                json_obj['absentDaysCount'] = len(absent_days)
                json_obj['absentDays'] = absent_days


        # if we are in fourth cell (fourth column)
        elif index == 4:
            json_obj['transferredVoteTo'] = {}
            transferred_vote_to = cell.findAll('div')
            json_obj['transferredVoteTo'] = transferred_vote_to[0].text


def get_absent_days(date_str):
    absences = []

    if len(date_str.split('.')) == 4 or len(date_str.split('.')) == 3:
        # e.g.: 29-30.11.2012г.

        absent_date_elems = date_str.split('.')
        absent_date_days = absent_date_elems[0].split('-')

        for absent_day_str in absent_date_days:
            absent_day = int(absent_day_str)
            absent_month = int(absent_date_elems[1])
            absent_year = int(absent_date_elems[2][0:4])

            absence_date_str = '%i/%i/%i' % (absent_day, absent_month, absent_year)
            absence_date = datetime.strptime(absence_date_str, "%d/%m/%Y")
            absences.append(absence_date)

    elif len(date_str.split('.')) == 6:
        # e.g.: 31.10.-01.11.2012г.
        absent_date_days = date_str.split('.-')

        first_month_str = absent_date_days[0]
        second_month_str = absent_date_days[1]

        second_month_elems = second_month_str.split('.')
        second_month_absent_day = int(second_month_elems[0])
        second_month_absent_month = int(second_month_elems[1])
        second_month_absent_year = int(second_month_elems[2][0:4])

        second_month_absence_str = '%i/%i/%i' % (second_month_absent_day, second_month_absent_month, second_month_absent_year)
        second_month_absence_date = datetime.strptime(second_month_absence_str, "%d/%m/%Y")

        first_month_elems = first_month_str.split('.')
        first_month_absent_day = int(first_month_elems[0])
        first_month_absent_month = int(first_month_elems[1])
        first_month_absent_year = second_month_absent_year

        first_month_absence_str = '%i/%i/%i' % (first_month_absent_day, first_month_absent_month, first_month_absent_year)
        first_month_absence_date = datetime.strptime(first_month_absence_str, "%d/%m/%Y")

        absences.append(first_month_absence_date)
        absences.append(second_month_absence_date)

    else:
        error_msg = 'Unsupported date pattern %s' % date_str
        print error_msg
        raise ValueError(error_msg)

    return absences


def fill_temp_doc_with_data(cell, index, temp_data):
    # But first, let's check if any td has rowspan
    if has_rowspan(cell) is True:

        # if td with index 2 has rowspan than get the rowspan value and cell text
        # in order to pass its value to other table rows
        if index == 2 and temp_data['reason']['counter'] is 0:
            span_nm_val = get_rowspan(cell)
            temp_data['reason']['counter'] = int(span_nm_val)

            # since table cell has more than one div, store its div value in array
            reasons = cell.findAll('div')
            temp_data['reason']['value'] = reasons[0].text

            if len(reasons) > 1:
                temp_data['reasonDetail'] = reasons[1].text.replace('&nbsp;', '').replace('(', '').replace(')', '')
            else:
                temp_data['reasonDetail'] = ''

        # if td with index 3 has rowspan than get the rowspan value and cell text
        # in order to pass its value to other table rows
        elif index == 3 and temp_data['date']['counter'] is 0:
            span_dt_val = get_rowspan(cell)
            temp_data['date']['counter'] = int(span_dt_val)
            date = cell.findAll('div')
            temp_data['date']['value'] = date[0].text


def scrape_mp_link_data(tp, br2, br3, mp_count):

    for index, link in enumerate(br2.links(text_regex=tp)):

        link_deputy_url = "http://www.kenesh.kg" + str(link.url)
        json_obj = {}

        # Let's do slicing
        text = link.text
        deputy_data = text.split()

        # scrape mp's party
        get_mp_party(deputy_data, json_obj, tp)

        # extract mp's first name and last name from link text
        get_mps_first_and_last_name(deputy_data, json_obj, tp)

        # Open mp's profile page
        respose = br3.open(link_deputy_url)

        get_image_url(index, respose, json_obj)

        # Get record of absences:
        json_obj['absences'] = get_absence_record(json_obj['firstName'], json_obj['lastName'])

        # insert data to database
        print "%i: %s %s" % (mp_count, json_obj['lastName'], json_obj['firstName'])
        mp_count = mp_count + 1

        db.deputies.insert(json_obj)


def get_mps_first_and_last_name(deputy_data, json_obj, party_tp):

    if party_tp == "Фракция":
        if len(deputy_data) == 5:
            deputy_l_name = deputy_data[0]
            if (deputy_data[2] != "-"):
                deputy_f_name = deputy_data[1] + " " + str(deputy_data[2])
            else:
                deputy_f_name = deputy_data[1]
        elif len(deputy_data) > 5:
            deputy_l_name = deputy_data[0]
            if deputy_data[2] != "-":
                deputy_f_name = str(deputy_data[1]) + " " + str(deputy_data[2])
            else:
                deputy_f_name = str(deputy_data[1])

    elif party_tp == "депутатская группа":
        if len(deputy_data) == 6:
            deputy_l_name = deputy_data[0]
            if (deputy_data[2] != "-"):
                deputy_f_name = deputy_data[1] + " " + str(deputy_data[2])
            else:
                deputy_f_name = deputy_data[1]
        elif len(deputy_data) == 7:
            deputy_l_name = deputy_data[0]
            if deputy_data[2] != "-":
                deputy_f_name = str(deputy_data[1]) + " " + str(deputy_data[2])
            else:
                deputy_f_name = str(deputy_data[1])
        elif len(deputy_data) == 8:
            deputy_l_name = deputy_data[0]
            deputy_f_name = deputy_data[1] + " " + str(deputy_data[2])

    elif party_tp == "АБДЫРАХМАНОВ Омурбек":
        deputy_l_name = deputy_data[0]
        deputy_f_name = deputy_data[1]

    elif party_tp == "ЖЭЭНБЕКОВ Равшан Бабырбекович":
        deputy_l_name = deputy_data[0]
        deputy_f_name = deputy_data[1] + " " + str(deputy_data[2])

    json_obj['firstName'] = deputy_f_name
    json_obj['lastName'] = deputy_l_name

    json_obj['firstNameLatin'] = unidecode(unicode(deputy_f_name, "utf-8"))
    json_obj['lastNameLatin'] = unidecode(unicode(deputy_l_name, "utf-8"))


def get_mp_party(deputy_data, json_obj, party_tp):
    # extract mp's party from link text
    if party_tp == "Фракция":
        if (deputy_data[-2] != "Фракция"):
            if deputy_data[-2] != "-Фракция":
                mp_party = str(deputy_data[-2]) + " " + str(deputy_data[-1])
            elif deputy_data[-2] == "-Фракция":
                mp_party = str(deputy_data[-1])
        else:
            mp_party = str(deputy_data[-1])

    elif party_tp == "депутатская группа":
        # extract mp's party from link text
        if (deputy_data[-2] != "группа"):
            mp_party = str(deputy_data[-2]) + " " + str(deputy_data[-1])
        else:
            mp_party = str(deputy_data[-1])

    elif party_tp == "АБДЫРАХМАНОВ Омурбек":
        mp_party = "независимый"
        party_tp = ''

    elif party_tp == "ЖЭЭНБЕКОВ Равшан Бабырбекович":
        mp_party = "беспартийный"
        party_tp = ''

    print "this is party: " + mp_party
    group = {
        'type': party_tp,
        'name': mp_party.replace('«', '').replace('»', '').replace('"', ''),
        'fullName': party_tp + mp_party
    }
    json_obj['group'] = group


def get_image_url(index, respose, json_obj):

    # Read content of the link and load it in soup
    html_content = respose.read()
    mp_soup = BeautifulSoup(html_content)
    if mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"}):
        div_content = mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"})

        div_cnt_soup = div_content
        # Scrape image url from website
        # Question mark by default image
        img_url = 'http://www.preternia.com/wp-content/uploads/2014/01/1493237_719399828079185_996651153_n.jpg'

        # Scrape mp's image url from profile page
        img_content = div_cnt_soup.findAll('img')
        for img in img_content:
            if not img['src'].startswith("../"):
                if (index == 98) and (img['height'] != "0"):
                    img_src = str(img['src'])
                    if img_src.startswith('http'):
                        img_url = str(img['src'])
                    else:
                        img_url = "http://www.kenesh.kg" + str(img['src'])
                else:
                    img_src = str(img['src'])
                    if img_src.startswith('http'):
                        img_url = str(img['src'])
                    else:
                        img_url = "http://www.kenesh.kg" + str(img['src'])

        json_obj['imgUrl'] = img_url


def get_absence_record(first_name, last_name):

    absences = {
        'sessions': {
            'count': 0,
            'sessions': []
        },
        'days': {
            'count': 0,
            'days': []
        }
    }

    absence_cursor = db.absence.find({
        'lastName': {"$regex": last_name, '$options': 'i'}, #use reges to ignore cases
        'firstName': first_name
    })

    for absence in absence_cursor:

        sa = {}

        if 'reason' in absence:
            sa['reason'] = absence['reason']

        if 'reasonDetail' in absence:
            sa['detail'] = absence['reasonDetail']

        if 'sessionDate' in absence:
            sa['date'] = absence['sessionDate']

        if 'transferredVoteTo' in absence:
            sa['transferredVoteTo'] = absence['transferredVoteTo']

        if 'source' in absence:
            sa['source'] = absence['source']

        absences['sessions']['sessions'].append(sa)

        for day in absence['absentDays']:
            absences['days']['days'].append(day)

    # sort the days
    absences['days']['days'].sort()

    if len(absences['days']['days']) > 0:
        absences['since'] = absences['days']['days'][0]

    absences['sessions']['count'] = len(absences['sessions']['sessions'])
    absences['days']['count'] = len(absences['days']['days'])

    return absences


def download_bio_images():
    '''
    Dowload all of the bio images.
    '''
    print '\nDownloading bio images...'

    '''
    # Get the path to this scraper's home directory.
    par_dir = os.path.join(__file__, os.pardir)
    par_dir_abs_path = os.path.abspath(par_dir)
    app_dir = os.path.dirname(par_dir_abs_path)

    # Get all of the bios
    docs = db.deputies.find()

    # For each bio, get the image
    for doc in docs:
        first_name = doc['firstName']
        last_name = doc['lastName']

        first_name_lat = doc['firstNameLatin']
        last_name_lat = doc['lastNameLatin']

        img_url = doc['imgUrl']

        print ''
        print "%s %s" % (last_name, first_name)
        print "%s %s" % (last_name_lat, first_name_lat)
        print img_url

        if img_url != '':
            img_filename = "%s/webapp/app/static/img/%s %s.jpg" % (app_dir, last_name_lat, first_name_lat)
            urllib.urlretrieve(img_url, img_filename)

            THUMB_SIZE = 300, 300
            img = Image.open(img_filename)
            width, height = img.size

            if width > height:
               delta = width - height
               left = int(delta/2)
               upper = 0
               right = height + left
               lower = height
            else:
               delta = height - width
               left = 0
               upper = int(delta/2)
               right = width
               lower = width + upper

            img = img.crop((left, upper, right, lower))
            img.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
            img.save(img_filename, "JPEG")
    '''

    print '\nDownload complete!'


# Check if the table cell(td) has attribute rowspan and return the value of it
def get_rowspan(cell):
    for attr in cell.attrs:
        if attr[0] == 'rowspan':
            return attr[1]


# Check if the table cell(td) has attribute rowspan
def has_rowspan(cell):
    for attr in cell.attrs:
        if attr[0] == 'rowspan':
            return True
    return False

# Execute scraper
scraper()
