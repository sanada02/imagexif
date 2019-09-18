import os
import time
import sys
import datetime
import requests
from PIL import Image #pip install pillow
from PIL.ExifTags import TAGS, GPSTAGS

def reverse_geocoding(latitude, longitude):
    if latitude is None or longitude is None:
        return "撮影場所不明"

    url = 'https://map.yahooapis.jp/geoapi/V1/reverseGeoCoder'
    payload = {'lat': latitude, 'lon': longitude, 'appid': 'your-app-id',
               'output':'json'}
    try:
        r = requests.get(url, params=payload)
        time.sleep(1)
        data = r.json()
        if 'AddressElement' in data['Feature'][0]['Property']:
            return data['Feature'][0]['Property']['AddressElement'][0]['Name']+\
                    data['Feature'][0]['Property']['AddressElement'][1]['Name']
        else:
            return data['Feature'][0]['Property']['Country']['Name'] #住所が取得できない場合は国名のみ
    except:
        return 'error'

def convert_decimal(gpsinfo):
    gpsresults = {}
    for key in ['Latitude', 'Longitude']:
        if 'GPS'+key in gpsinfo and 'GPS'+key+'Ref' in gpsinfo:
            e = gpsinfo['GPS'+key]
            ref = gpsinfo['GPS'+key+'Ref']
            gpsresults[key] = (e[0][0]/e[0][1] + e[1][0]/e[1][1] / 60 + e[2][0]/e[2][1] / 3600)\
                           * (-1 if ref in ['S', 'W'] else 1)

    if 'Latitude' in gpsresults and 'Longitude' in gpsresults:
        return gpsresults['Latitude'], gpsresults['Longitude']
    else:
        return None, None

def get_exif(filename):
    exif = Image.open(filename)._getexif()

    #results = [date, latitude, longitude]
    results = ["撮影日不明", None, None]

    if exif is None:
        return results

    exif_dict = {}
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag == "GPSInfo":
            gps_data = {}
            for t in value:
                gps_tag = GPSTAGS.get(t, t)
                gps_data[gps_tag] = value[t]
            exif_dict[tag] = gps_data
        else:
            exif_dict[tag] = value

    if 'DateTimeOriginal' in exif_dict:
        date = datetime.datetime.strptime(exif_dict['DateTimeOriginal'][:10], '%Y:%m:%d')
        results[0] = date.strftime('%Y-%m-%d')
    #'DateTimeDigitized'と'DateTime'は最初の撮影日でない可能性があるので省略可
    elif 'DateTimeDigitized' in exif_dict:
        date = datetime.datetime.strptime(exif_dict['DateTimeDigitized'][:10], '%Y:%m:%d')
        results[0] = date.strftime('%Y-%m-%d')
    elif 'DateTime' in exif_dict:
        date = datetime.datetime.strptime(exif_dict['DateTime'][:10], '%Y:%m:%d')
        results[0] = date.strftime('%Y-%m-%d')

    if 'GPSInfo' in exif_dict:
        gpsresults = convert_decimal(exif_dict['GPSInfo'])
        results[1] = gpsresults[0]
        results[2] = gpsresults[1]

    return results

def main():
    i = 0
    #以下はカレントディレクトリが整理したい画像フォルダであることが前提(サブディレクトリは整理対象に含まない)
    for file in os.listdir():
        base, ext = os.path.splitext(file)
        ext = ext.lower()
        if ext == '.jpg' or ext == '.jpeg':
            i += 1
            exif = get_exif(file)
            date = exif[0]
            place = reverse_geocoding(exif[1], exif[2])
            if place == 'error':
                print('地名取得中にエラーが発生しました')
                sys.exit()
            print("{}番目のファイルを移動中...".format(i))
            print(place)
            print(date)
            os.renames(file, '{}\{}\{}'.format(place, date, file))
    print("ファイルの整理が完了しました")

if __name__ == '__main__':
    main()
