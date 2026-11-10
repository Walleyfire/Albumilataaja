import unittest
from unittest.mock import Mock
import spotify_catalog as catalog

ID='6KbCFHgM4basg1TvK3oEzv'
ALBUM='5G9yb1cukFiWzOKqDPeqo3'

class SpotifyCatalogTests(unittest.TestCase):
    def test_eppu_artist_search_does_not_use_track_only_search(self):
        api=Mock()
        api.query_artists.return_value={'data':{'searchV2':{'artists':{'items':[
            {'data':{'uri':'spotify:artist:'+ID,'profile':{'name':'Eppu Normaali'}}},
            {'data':{'uri':'spotify:track:'+ALBUM,'profile':{'name':'Wrong result'}}}
        ]}}}}
        self.assertEqual(catalog.search_artists('Eppu Normaali',api),[{'artist':'Eppu Normaali','spotify_id':ID}])
        api.query_artists.assert_called_once_with('Eppu Normaali',limit=12)
        api.search.assert_not_called()

    def test_all_pages_and_singles_filter(self):
        def group(key,title,kind):
            return {'releases':{'items':[{'uri':'spotify:album:'+key,'name':title,'type':kind,'date':{'year':2016}}]}}
        one=group(ALBUM,'Ratina','ALBUM')
        two=group('2fGjFEJoJ21Qshx8c91gbw','Single','SINGLE')
        api=Mock(); api.paginate_artist_discography.return_value=iter([[one],[one,two]])
        albums=catalog.list_albums(ID,api=api)
        self.assertEqual(len(albums),2)
        self.assertEqual(albums[0]['title'],'Ratina')
        api.paginate_artist_discography.assert_called_once_with(ID,section='all',order='DATE_DESC')
        self.assertEqual(len(catalog.parse_releases([one,two],False)),1)

    def test_valid_artist_link_and_response_errors(self):
        self.assertEqual(catalog.artist_id('https://open.spotify.com/intl-fi/artist/'+ID+'?si=test'),ID)
        for link in ['https://open.spotify.com.evil.test/artist/'+ID,'https://open.spotify.com/album/'+ALBUM]:
            with self.assertRaises(ValueError): catalog.artist_id(link)
        with self.assertRaises(ValueError): catalog.parse_artists({'error':'unavailable'})

if __name__=='__main__': unittest.main()
