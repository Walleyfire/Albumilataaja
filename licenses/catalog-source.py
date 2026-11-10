"""Spotify catalog worker. GPL-3.0-or-later; separate process from the UI.

Uses SpotAPI for public catalog metadata only. No account login or audio access.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import requests

def artist_id(value):
    if not value.startswith('https://'):
        raise ValueError('Spotify-artistilinkin pitää alkaa https://open.spotify.com/artist/.')
    url=urlparse(value)
    match=re.fullmatch(r'/(?:intl-[a-z]+/)?artist/([A-Za-z0-9]{22})/?',url.path)
    if url.hostname!='open.spotify.com' or not match:
        raise ValueError('Julkaisujen hakuun tarvitaan Spotify-artistin linkki.')
    return match.group(1)

def parse_artists(response):
    items=response.get('data',{}).get('searchV2',{}).get('artists',{}).get('items')
    if items is None: raise ValueError('Spotify palautti odottamattoman hakuvastauksen.')
    artists=[]; seen=set()
    for item in items:
        data=item.get('data') or {}; uri=data.get('uri','')
        name=data.get('profile',{}).get('name','').strip()
        if not re.fullmatch(r'spotify:artist:[A-Za-z0-9]{22}',uri) or not name: continue
        key=uri.rsplit(':',1)[-1]
        if key not in seen: seen.add(key); artists.append({'artist':name,'spotify_id':key})
    return artists

def parse_releases(items,include_singles=True):
    result=[]; seen=set()
    for group in items:
        for release in group.get('releases',{}).get('items',[]):
            uri=release.get('uri',''); kind=release.get('type','ALBUM').upper()
            if not re.fullmatch(r'spotify:album:[A-Za-z0-9]{22}',uri): continue
            if not include_singles and kind in ['SINGLE','EP']: continue
            key=uri.rsplit(':',1)[-1]
            if key in seen: continue
            seen.add(key)
            date=release.get('date') or {}
            result.append({'title':release.get('name') or 'Albumi','year':date.get('year') or '',
                           'date':date.get('isoString') or '',
                           'kind':{'ALBUM':'Albumi','COMPILATION':'Kokoelma'}.get(kind,'Single / EP'),
                           'spotify_url':'https://open.spotify.com/album/'+key})
    return result

def create_client():
    # Use bounded requests instead of curl transport, which timed out on this
    # Windows environment. SpotAPI still handles the public catalog protocol.
    from spotapi import Artist
    from spotapi.http.request import TLSClient
    class RequestsClient(TLSClient):
        def __init__(self):
            super().__init__('chrome120','',auto_retries=0)
            self.http=requests.Session()
        def build_request(self,method,url,**kwargs):
            headers=dict(self.headers); headers.update(kwargs.pop('headers',{}))
            return self.http.request(method,url,headers=headers,timeout=(10,20),**kwargs)
    return Artist(client=RequestsClient())

def search_artists(query,api=None):
    query=query.strip()
    if query.startswith('https://'):
        key=artist_id(query)
        api=api or create_client()
        response=api.get_artist(key)
        name=response.get('data',{}).get('artistUnion',{}).get('profile',{}).get('name')
        if not name: raise ValueError('Spotify-artistin tietoja ei löytynyt.')
        return [{'artist':name,'spotify_id':key}]
    if query.lower().startswith('artist:'): query=query.split(':',1)[1].strip()
    if not query: raise ValueError('Kirjoita artistin nimi.')
    api=api or create_client()
    return parse_artists(api.query_artists(query,limit=12))

def list_albums(key,include_singles=True,api=None):
    if not re.fullmatch('[A-Za-z0-9]{22}',key): raise ValueError('Virheellinen artistitunniste.')
    api=api or create_client(); items=[]
    for page in api.paginate_artist_discography(key,section='all',order='DATE_DESC'):
        items.extend(page)
    return parse_releases(items,include_singles)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('operation',choices=['search','albums'])
    parser.add_argument('value'); parser.add_argument('output',type=Path); parser.add_argument('--albums-only',action='store_true')
    args=parser.parse_args()
    try:
        data={'artists':search_artists(args.value)} if args.operation=='search' else {'albums':list_albums(args.value,not args.albums_only)}
        args.output.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return 0
    except Exception as error:
        args.output.write_text(json.dumps({'error':'Spotify-tietojen haku epäonnistui: '+str(error)},ensure_ascii=False),encoding='utf-8')
        return 1

if __name__=='__main__': raise SystemExit(main())
