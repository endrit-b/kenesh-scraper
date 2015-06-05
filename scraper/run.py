# -*- coding: utf-8 -*-
from pymongo import MongoClient
import mechanize
from BeautifulSoup import BeautifulSoup
import re
import urllib
import os
import PIL
from PIL import Image

client = MongoClient()
db = client.kenesh


def scraper():

<<<<<<< HEAD
    # Execute MP's bio data scraper
    #scrape_absence_data()

    # Execute MP's bio data scraper
    #scrape_mp_bio_data()

    # Sync Data of absentees with their bio data
    sync_mp_data()
=======
    # execute absence data scraper.
    scrape_absence_data()

    # execute MP's bio data scraper.
    scrape_mp_bio_data()
>>>>>>> fb524ca08884e0ec431a4a7cc3ceef3158e6a2d3

    # Download bio images and render thumbnails.
    #download_bio_images()


# Funtction whic will scrape MP's absence data
def scrape_absence_data():

    db.absence.remove({})
    print "Scraping parliament session absentee data..."

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
        link_url = "http://kenesh.kg" + str(link.url)

        print ''
        print 'SESSION: %s' % link_url

        # Open absentees link
        respose = br1.open(link_url)
        # Read content of the link and load it in soup
        html_content = respose.read()
        soup = BeautifulSoup(html_content)
        if soup.find('table', style=lambda x: x and x.startswith('width:102.84')):
            table = soup.find('table', style=lambda x: x and x.startswith('width:102.84'))
        elif soup.find('table', style=lambda x: x and x.startswith('border-bottom: medium none; border-left')):
            table = soup.find('table', style=lambda x: x and x.startswith('border-bottom: medium none; border-left'))
        table_soup = table
        table_rows = table_soup.findAll('tr')

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
                    if len(row.findAll('td')) < 5:

                        if cell.findAll('div'):
                            # let's just check for div(s) in td and get its value

                            # if we are in first cell (first column)
                            if index == 1:
                                names = cell.findAll('div')
                                if len(names) > 1:
                                    # Get first name. Sometimes it has multiple whitespaces in between two names.
                                    # We replace those multiple whitespaces with just one space using regex
                                    json_obj['firstName'] = re.sub(r' +', ' ', names[1].text)

                                json_obj['lastName'] = names[0].text

                            # if we are in third cell (third column)
                            elif index == 2:
                                json_obj['transferredVoteTo'] = {}
                                transferred_vote_to = cell.findAll('div')
                                json_obj['transferredVoteTo'] = transferred_vote_to[0].text

                        # if this row doesnt have name and date value td(s) because of spanning
                        # let's get them from temporary json we build for this reason
                        if temp_data['reason']['counter'] > 0:
                            json_obj['reason'] = temp_data['reason']['value']
                            if temp_data['reasonDetail'] != '':
                                json_obj['reasonDetail'] = temp_data['reasonDetail']
                        if temp_data['date']['counter'] > 0:
                            json_obj['sessionDate'] = temp_data['date']['value']
                    else:
                        if cell.findAll('div'):
                            # But first, let's check if any td has rowspan
                            if has_rowspan(cell) is True:

                                # if td with index 2 has rowspan than get the rowspan value and cell text
                                # in order to pass its value to other table rows
                                if index == 2 and temp_data['reason']['counter'] is 0:
                                    span_nm_val = get_rowspan(cell)
                                    temp_data['reason']['counter'] = int(span_nm_val)
                                    # since table cell has more than one div, store its div value in array
                                    reasons = cell.findAll('div')
                                    temp_data['reason']['value']= reasons[0].text

                                    if len(reasons) > 1:
                                        temp_data['reasonDetail'] = reasons[1].text
                                # if td with index 3 has rowspan than get the rowspan value and cell text
                                # in order to pass its value to other table rows
                                elif index == 3 and temp_data['date']['counter'] is 0:
                                    span_dt_val = get_rowspan(cell)
                                    temp_data['date']['counter'] = int(span_dt_val)
                                    date = cell.findAll('div')
                                    temp_data['date']['value'] = date[0].text

                            # if we are in first cell (first column)
                            if index == 1:
                                names = cell.findAll('div')
                                if len(names) > 1:
                                    json_obj['firstName'] = names[1].text
                                json_obj['lastName'] = names[0].text

                            # if we are in second cell (second column)
                            elif index == 2:
                                json_obj['reason'] = {}
                                reasons = cell.findAll('div')
                                json_obj['reason'] = reasons[0].text

                                if len(reasons) > 1:
                                    json_obj['reasonDetail'] = reasons[1].text

                            # if we are in third cell (third column)
                            elif index == 3:
                                json_obj['sessionDate'] = {}
                                date = cell.findAll('div')
                                json_obj['sessionDate'] = date[0].text

                            # if we are in fourth cell (fourth column)
                            elif index == 4:
                                json_obj['transferredVoteTo'] = {}
                                transferred_vote_to = cell.findAll('div')
                                json_obj['transferredVoteTo'] = transferred_vote_to[0].text

            # Time to save the json document in mongodb
            db.absence.insert(json_obj)

            if 'firstName' in json_obj:
                print "%i: %s %s" % (absence_count, json_obj['lastName'], json_obj['firstName'])
            else:
                print "%i: %s" % (absence_count, json_obj['lastName'])

            absence_count = absence_count + 1

            # Decrement counters as the rows pass
            if temp_data['reason']['counter'] > 0:
                temp_data['reason']['counter'] -= 1
            if temp_data['date']['counter'] > 0:
                temp_data['date']['counter'] -= 1

    print "Scraping complete"


# Funtction which will scrape MP's bio data
def scrape_mp_bio_data():

    db.deputies.remove({})
    print "Scraping members of parliament bio..."

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

    # Iterate links of factions
    for index, link in enumerate(br2.links(text_regex="Фракция")):

        link_deputy_url = "http://www.kenesh.kg" + str(link.url)
        json_obj = {}

        # Let's do slicing
        text = link.text
        deputy_data = text.split()

        # extract mp's party from link text
        if (deputy_data[-2] != "Фракция"):
            if deputy_data[-2] != "-Фракция":
                mp_party = str(deputy_data[-2]) + " " + str(deputy_data[-1])
        else:
            mp_party = str(deputy_data[-1])

        group = {
            'type': "Фракция",
            'name': mp_party
        }
        json_obj['group'] = group

        # extract mp's first name and last name from link text
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

        json_obj['firstName'] = deputy_f_name
        json_obj['lastName'] = deputy_l_name

        # Open mp's profile page
        respose = br3.open(link_deputy_url)
        # Read content of the link and load it in soup
        html_content = respose.read()
        mp_soup = BeautifulSoup(html_content)
        if mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"}):
            div_content = mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"})

            div_cnt_soup = div_content
            img_url = ''
            # Scrape mp's image url from profile page
            img_content = div_cnt_soup.findAll('img')
            for img in img_content:
                if not img['src'].startswith("../"):
                    if (index == 98) and (img['height'] != "0"):
                        img_src = str(img['src'])
                        if img_src.startswith('http'):
                            img_url = str(img['src'])
                        else:
                            print "http://www.kenesh.kg" + str(img['src'])
                    else:
                        img_src = str(img['src'])
                        if img_src.startswith('http'):
                            img_url = str(img['src'])
                        else:
                            img_url = "http://www.kenesh.kg" + str(img['src'])
            json_obj['imgUrl'] = img_url
            # Scrape mp's bio from profile page
            '''
            if div_cnt_soup.findAll('p', attrs={'class': 'MsoNormal'}):
                mp_bio = div_cnt_soup.findAll('p', attrs={'class': 'MsoNormal'})
                #print mp_bio
                bio_txt = mp_bio[0].text
            elif div_cnt_soup.findAll('p', attrs={'style': "text-align: justify"}):
                mp_bio = div_cnt_soup.findAll('p', attrs={'style': "text-align: justify"})
                bio_txt = mp_bio[0].text
            '''
        # insert data to database
        db.deputies.insert(json_obj)

    # Iterate links of group deputies
    for index, link in enumerate(br2.links(text_regex="депутатская группа")):

        link_deputy_url = "http://www.kenesh.kg" + str(link.url)
        json_obj = {}
        text = link.text

        deputy_data = text.split()

        # extract mp's party from link text
        if (deputy_data[-2] != "группа"):
            mp_party = str(deputy_data[-2]) + " " + str(deputy_data[-1])
        else:
            mp_party = str(deputy_data[-1])
        group = {
            'type': "депутатская группа",
            'name': mp_party
        }
        json_obj['group'] = group

        # extract mp's first name and last name from link text
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

        json_obj['firstName'] = deputy_f_name
        json_obj['lastName'] = deputy_l_name
        #print(deputy_l_name + ", " + deputy_f_name + " " + deputy_l_name)

        # Open mp's profile page
        respose = br3.open(link_deputy_url)
        # Read content of the link and load it in soup
        html_content = respose.read()
        mp_soup = BeautifulSoup(html_content)
        if mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"}):
            div_content = mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"})

            div_cnt_soup = div_content
            img_url = ''
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
        # insert data to database
        db.deputies.insert(json_obj)

    print "Scraping complete!"


<<<<<<< HEAD
# Sync Data of absentees and their bio data
def sync_mp_data():
    cursor = db.deputies.find()
    for doc in cursor:

        json_obj = {'group': doc['group'], 'imgUrl': doc['imgUrl']}

        f_name = doc['firstName']
        last_name = doc['lastName']

        db.absence.update({
            'lastName': {"$regex": last_name, '$options': 'i'},
            'firstName': {"$regex": f_name, '$options': 'i'}},
            {"$set": json_obj})

=======
def download_bio_images():
    '''
    Dowload all of the bio images.
    '''
    print 'Downloading bio images...'

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
        img_url = doc['imgUrl']

        print ''
        print "%s %s" % (last_name, first_name)
        print img_url

        if img_url != '':
            img_filename = "%s/webapp/app/static/img/%s %s.jpg" % (app_dir, last_name, first_name)
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
       
    print 'Download complete!'
>>>>>>> fb524ca08884e0ec431a4a7cc3ceef3158e6a2d3

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
