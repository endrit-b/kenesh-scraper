# kenesh-scraper
Scraping data from the Supreme Council's website


What Is It?
===========
A script that scrapes data from Kyrgyzstan Supreme Council's website: http://www.kenesh.kg/

In particular from the list of members who missed sessions: http://www.kenesh.kg/RU/Folders/4258-Uchastie_deputatov_v_zasedaniyax_ZHogorku_Kenesha.aspx

And from members bio pages:
http://www.kenesh.kg/RU/Folders/235-Deputaty.aspx

How Does It Work?
=================

* [Mechanize](http://wwwsearch.sourceforge.net/mechanize/) to simulate browser requests.
* [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) to extract data from HTML.
* [Pythong Image Library (PIL)](http://www.pythonware.com/products/pil/) to render thumbnails from downloaded bio images.


Installing and Running
======================
Prequisites on OSX:
1) Open your terminal and execute:  xcode-select --install
This is so that the install script can install PIL.
PIL is for image processing.

2) libjpg - needed so that PIL can create JPEG thumbnails from the downloaded parliament member bio image files.
Installing libjpg with brew: brew install libjpeg

Prequisites on Ubuntu:
sudo apt-get build-dep python-imaging
sudo apt-get install libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev
sudo pip install Pillow

So easy to install and run:
```
bash install.sh
bash run.sh
```
