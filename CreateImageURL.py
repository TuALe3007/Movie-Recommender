import csv

import torch  # Deep learning - NOT USED
import numpy as np  # Data analysis
import pandas as pd  # Data analysis
import matplotlib.pyplot as plt  # Plot data
import time
from bs4 import BeautifulSoup # For reading html
import urllib.parse
import urllib.request
from urllib.error import HTTPError


def create_image_links():
    row_names = ['movieId', 'imageURL']
    links = pd.read_csv('links.csv', converters={'imdbId': str})
    domain = 'https://www.imdb.com'
    extension = '/?ref_=fn_al_tt_1'  # to avoid 308 error
    count = 0
    for row in links.iterrows():
        if count < 2760:
            count = count + 1
            print(count)
            continue

        movie_id = row[1]['imdbId']
        movie_real_id = row[1]['movieId']
        movie_url = domain + '/title/tt' + movie_id + extension    # IMDB movie URL
        req = urllib.request.Request(url=movie_url, headers={'User-Agent': 'Mozilla/5.0'})  # headers to avoid 403 error

        try:
            html = urllib.request.urlopen(req).read()
            soup = BeautifulSoup(html, 'html.parser')   # Reading the html of the page

            # Getting the images:
            try:
                image_url = soup.find('div', class_='ipc-poster').img['src']
                image_url = ''.join(image_url.partition('_')[0]) + 'jpg'
                print(image_url)
                with open('image.csv', 'a', newline='') as output:
                    writer = csv.writer(output, delimiter=',')
                    writer.writerow([movie_real_id, image_url])
                continue
            # If no images found, pass
            except TypeError:
                pass
        except HTTPError:
            pass



if __name__ == "__main__":
    create_image_links()

