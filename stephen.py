"""
Scrape the QI transcripts site and format the data somewhat
Save to json for future processing without hitting the site
"""


import json
import re
import urllib2
from bs4 import BeautifulSoup
_NBSP = u'\xa0'
index_url = 'https://sites.google.com/site/qitranscripts/transcripts'


def get_qi(url):
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    main_table = soup.find('table',
                           attrs={'class': 'sites-layout-name-one-column'})
    sub_tables = main_table.findAll('table')

    studium_excitat = {}

    for i, season in enumerate(sub_tables):
        studium_excitat[i + 1] = []
        for episode in season.findAll('tr'):
            ep_data = {}
            episode_title = episode.findAll('td')[1].text
            if episode.find('a'):
                episode_link = episode.find('a')['href']
                episode_code, namelist = episode.find('a')\
                                                .text.replace(_NBSP, ' ')\
                                                .split(' ', 1)
                ep_data['code'] = episode_code
                ep_data['title'] = episode_title
                ep_data['source'] = episode_link
                ep_data['guests'] = namelist.strip().split(',')

                guest_first_names = [x.strip().split(" ")[0] for x in
                                     namelist.strip().split(',')]

                ep_data['transcript'] = get_transcript(episode_link,
                                                       guest_first_names) if episode_link else None
                studium_excitat[i + 1].append(ep_data)
            else:
                print 'Episode is missing a link: '.format(episode_title)

    return studium_excitat


def clean_html(html):
    soup = BeautifulSoup(html)
    for match in soup.findAll('br'):
        match.unwrap()
    for match in soup.findAll('span'):
        match.unwrap()
    return soup.get_text().replace(_NBSP, ' ')


def get_transcript(url, guests):
    # stephen and alan not included in metadata
    # was alan ever absent from an episode, wasnt there one where he was dressed as a chicken
    guests.append('Stephen')
    guests.append('Alan')
    guest_re = '|'.join(['>' + x + '<' for x in guests])
    transcript = []
    stream = urllib2.urlopen(url)
    data = stream.read()
    data = data.replace('<span>', '').replace('</span>', '')  # specific case for season 1
    segments = re.compile('(' + guest_re + ')', re.IGNORECASE).split(data)

    for i, s in enumerate(segments):
        if re.match(guest_re, s, re.IGNORECASE):
            # segments = segments[1:] # trim up to first
            # the tags around the names vary across episodes, so match with angle brackets only
            # then strip them from the name
            # and add the back in to the start of sentence so soup can strip the html
            transcript.append({
                'name': clean_html(segments[i]).replace('<', '').replace('>', ''),
                'sentence': clean_html('<' + segments[i+1])  # assuming it wont end on a name, else it will crap out
            })
    return transcript


jdata = get_qi(index_url)

# # validate
# for i in data:
#     if not data[i]['transcript']:
#         print 'Validation Error: {}'.format(data[i]['code'])

with open('raw/scrape_01.json', 'w') as f:
    json.dump(jdata, f, indent=4)
