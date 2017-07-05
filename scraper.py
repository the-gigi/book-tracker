# import os
# import sys
# import re
# from collections import defaultdict
#
# import requests
# import time
# from requests.auth import HTTPBasicAuth
# from bs4 import BeautifulSoup
# from pprint import pprint as pp
# from contextlib import closing
# from selenium.webdriver import Chrome # pip install selenium
# from selenium.webdriver.support.ui import WebDriverWait
#
#
# base_url = 'http://vrviu:vrviu@staging.vrideo.com/'
# user = 'vrviu'
# password = 'vrviu'
# script_dir = os.path.abspath(os.path.dirname(__file__))
# site_dir = os.path.join(script_dir, 'site')
# auth = HTTPBasicAuth('vrviu', 'vrviu')
#
# metadata = dict(categories=defaultdict(dict))
#
# all_video_ids = set()
#
#
# def get_page(path, filename, use_requests):
#     # Munge path and filename
#     if filename is None:
#         filename = path[8:] if path.startswith('/browse/') else path
#
#     if not filename.startswith(site_dir):
#         filename = os.path.join(site_dir, filename)
#     filename = os.path.normpath(os.path.abspath(filename))
#     if not filename.endswith('.html'):
#             filename += '.html'
#
#     # Check if local file already exists
#     if os.path.isfile(filename):
#         try:
#             content = open(filename).read()
#         except Exception as e:
#             content = open(filename, 'rb').read().decode('utf-8')
#         if len(content) > 0:
#             return content
#
#     # Ensure parent directory exists
#     parent_dir = os.path.dirname(filename)
#     if not os.path.isdir(parent_dir):
#         os.makedirs(parent_dir)
#
#     # Download
#     url = base_url + path
#     if use_requests:
#         r = requests.get(url, auth=auth)
#         content = r.content.decode('utf-8')
#     else:
#         # use firefox to get page with javascript generated content
#         with closing(Chrome()) as browser:
#             browser.get(url)
#             time.sleep(3)
#             # wait for the page to load
#
#             # WebDriverWait(browser, timeout=10).until(
#             # store it to string variable
#             content = browser.page_source
#
#     # save to local file
#     try:
#         open(filename, 'w').write(content)
#     except Exception as e1:
#         try:
#             open(filename, 'wb').write(bytes(content, 'utf-8'))
#         except Exception as e2:
#             print('Failed to download ', url)
#     return content
#
#
# def get_soup(path, filename=None, use_requests=False):
#     page = get_page(path, filename, use_requests)
#     return BeautifulSoup(page, 'html.parser')
#
#
# def download_all_pages(browse_page):
#     """
#     """
#     soup = get_soup(browse_page)
#     categories = soup.find_all('a', href=re.compile('/browse/'))
#     # Extract categories and sub-categories
#
#     for c in categories:
#         url = c.attrs['href']
#         if '\n' in c.text:
#             continue
#         category = dict(name=c.text, url=url, sub_categories={}, pages={})
#         print(category['name'])
#         metadata['categories'][url[len('/browse/'):]] = category
#         download_category(category)
#
#
# def download_category(category):
#     """
#     :param category:
#     """
#     soup = get_soup(category['url'])
#     # Check if there are sub-categories
#
#     # Find sub-categories
#     sub_categories = soup.find_all('a', href=re.compile(category['url']))
#     # Extract categories and sub-categories
#
#     for c in sub_categories:
#         tokens = c.attrs['href'].split('/') + ['']
#         category_name, sub_name = tokens[2:4]
#         if sub_name:
#             category['sub_categories'][sub_name] = dict(name=sub_name, pages={})
#         download_sub_category(category_name, sub_name)
#
#
# def download_sub_category(category_name, sub_category_name):
#     """
#
#     :return:
#     """
#     #
#     url = 'results?category={}&subcategory={}&sort=rating'.format(category_name, sub_category_name)
#     prefix = category_name + '-' + sub_category_name if sub_category_name else category_name
#
#     category = metadata['categories'][category_name]
#     if sub_category_name:
#         category = category['sub_categories'][sub_category_name]
#
#     filename = '{}-page-{}'.format(prefix, 1)
#     soup = get_soup(url, filename, use_requests=True)
#
#     download_video_page(category, 1, soup)
#     pages = soup.find_all('a', href=re.compile('page='))
#     for i in range(1, len(pages)):
#         url = 'results?category={}&subcategory={}&page={}&sort=rating'.format(category_name, sub_category_name, i + 1)
#         filename = '{}-page-{}'.format(prefix, i + 1)
#         soup = get_soup(url, filename, use_requests=True)
#         download_video_page(category, i + 1, soup)
#
#
# def download_video_page(category, page_index, soup):
#     """
#     :return:
#     """
#
#     videos = soup.find_all(lambda tag: 'data-video-id' in tag.attrs)
#     video_pages = category['pages']
#     video_pages[page_index] = {}
#     for v in videos:
#         vid = v.attrs['data-video-id']
#         video_pages[page_index][vid] = dict(video_id=vid)
#         all_video_ids.add(vid)
#
#     # Parse video metadata
#     items = soup.find_all(lambda t: t.attrs['class'] == ['row', 'results'])
#     for item in items:
#         vid = item.find(lambda t: 'data-id' in t.attrs).attrs['data-id']
#         thumbnail = '/api/v1/videos/{}/thumbnail'.format(vid)
#         title = item.find('a', {'class': 'black-link'}).content[0]
#         budges = item.find_all('span', {'class': 'badge-video'})
#         badges = [x.contents[0] for x in budges]
#         # What is this????
#         csapp = item.find(href='/csapp').contents[0]
#         desc = item.find('div', {'class': 'description'}).contents[0]
#         play_time = item.find('div', {'class': 'time'}).contents[0]
#         x = item.find_all(lambda t: t.attrs['class'] == ['lighter', 'gray'])
#         date, views = [o.trim() for o in next(x.children).split('·')]
#



def main():
    """

    :return:
    """
    # download_all_pages('browse.html')
    # pp(metadata)


if __name__ == '__main__':
    main()
