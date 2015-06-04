# -*- coding: utf-8 -*-
from pymongo import MongoClient, database
import mechanize
from BeautifulSoup import BeautifulSoup
from bson import ObjectId
#import re

client = MongoClient()
db = client.kenesh


def scraper():
    db.absence.remove({})
    db.deputies.remove({})

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

    for link in br.links(text_regex="Сведения об участии депутатов в заседаниях"):
        link_url = "http://kenesh.kg" + str(link.url)
        #"http://www.kenesh.kg/RU/Articles/4669-Svedeniya_ob_uchastii_deputatov_v_zasedaniyax_ZHK_7_marta_2012_goda.aspx"

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
        for row in table_rows[1:]:
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
                                    json_obj['firstName'] = names[1].text
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

            print json_obj
            # Time to save the json document in mongodb
            db.absence.insert(json_obj)

            # Decrement counters as the rows pass
            if temp_data['reason']['counter'] > 0:
                temp_data['reason']['counter'] -= 1
            if temp_data['date']['counter'] > 0:
                temp_data['date']['counter'] -= 1

        break



    '''
    ####### Scraping data from mp's page #######
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
    for index, link in enumerate(br2.links(text_regex="Фракция")):
        if index < 107:
            link_deputy_url = "http://www.kenesh.kg" + str(link.url)
            #"http://www.kenesh.kg/RU/Articles/297-ABDIEV_Kurmantaj__Frakciya_AtaZHurt.aspx"

            text = link.text
            deputy_data = text.split()
            # extract mp's party from link text
            if (deputy_data[-2] != "Фракция"):
                if deputy_data[-2] != "-Фракция":
                    mp_party = str(deputy_data[-2]) + " " + str(deputy_data[-1])
            else:
                mp_party = str(deputy_data[-1])

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

            # Open mp's profile page
            respose = br3.open(link_deputy_url)
            # Read content of the link and load it in soup
            html_content = respose.read()
            mp_soup = BeautifulSoup(html_content)
            if mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"}):
                div_content = mp_soup.find('div', attrs={'id': "ctl00_ctl00_CPHMiddle_pnlContent"})

                div_cnt_soup = div_content
                parag_content = div_cnt_soup.findAll('p', attrs={'style':"text-align: justify"})

                p_soup = parag_content
                print p_soup
                for sp in p_soup:
                    print sp

                    if sp.find('img')['src']:
                        img_attr = p_soup.find('img')['src']
                        if not img_attr.startswith('http://www.kenesh'):
                            print "http://www.kenesh.kg" + str(img_attr)
                        else:
                            print str(img_attr)

                print index
                print "------------------------"
        '''


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
