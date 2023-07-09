from lxml import html 
import requests
def check_if_new_latest_update():
    url = 'https://data.ris.ripe.net/rrc00/'
    r = requests.get(url).content 
    # time_ = html.fromstring(r).xpath("/html/body/table/tr[5]/td[3]/text()") 
    time_ = html.fromstring(r).xpath("/html/body/pre/a[@href='latest-update.gz']/following-sibling::text()") 
    print(time_[0].strip().split('      ')[0])
    # /html/body/pre/text()[287]
    # this_last_modified = time_[0]

check_if_new_latest_update()