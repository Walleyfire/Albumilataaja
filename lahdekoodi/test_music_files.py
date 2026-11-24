from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch
from music_files import youtube_identity,clean_title,publish_music
from mutagen.wave import WAVE
from mutagen.id3 import TIT2,TPE1,TXXX,TALB


class MusicFileTests(unittest.TestCase):
    def audio(self,path):
        with wave.open(str(path),'wb') as audio:
            audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(8000);audio.writeframes(b'\x00\x00'*800)
        data=WAVE(path);data.add_tags()
        data.tags.add(TIT2(encoding=3,text='01 - dirty title [AAAAAAAAAAA]'))
        data.tags.add(TPE1(encoding=3,text='Publisher channel'))
        data.tags.add(TXXX(encoding=3,desc='SOURCE',text='https://youtube.com/watch?v=AAAAAAAAAAA'))
        data.tags.add(TALB(encoding=3,text='Unwanted album'));data.save()
    def test_title_and_artist_are_separated_from_video_title_not_publisher(self):
        title,artists=youtube_identity({'title':'Ava Max - Ghost (Official Audio)','uploader':'Future House Music'})
        self.assertEqual(title,'Ghost');self.assertEqual(artists,['Ava Max'])
        title,artists=youtube_identity({'title':"Avicii - Levels (Skrillex Remix) [FULL]",'uploader':'Skrillex'})
        self.assertEqual(title,'Levels (Skrillex Remix)');self.assertEqual(artists,['Avicii'])
        self.assertEqual(youtube_identity({'track':'Alan Walker - Faded','artist':'Alan Walker'})[0],'Faded')
        self.assertEqual(youtube_identity({'id':'AAAAAAAAAAA','title':'01 - Alan Walker - Faded [AAAAAAAAAAA] (Official Video)'})[0],'Faded')
        self.assertEqual(youtube_identity({'title':'Clean Bandit - Rather Be','artists':['Clean Bandit','Jess Glynne']})[1],['Clean Bandit','Jess Glynne'])
    def test_only_presentation_labels_are_removed(self):
        self.assertEqual(clean_title('Faded (Official Music Video) [HD]'),'Faded')
        self.assertEqual(clean_title('Ghost [Official] [1080p]'),'Ghost')
        self.assertEqual(clean_title('Bulletproof (Official Music Video Remastered)'),'Bulletproof')
        self.assertEqual(clean_title('Song (Radio Edit) [Live at Wembley]'),'Song (Radio Edit) [Live at Wembley]')
        self.assertEqual(clean_title('Song (2011 Remaster)'),'Song (2011 Remaster)')
    def test_new_file_has_readable_name_and_only_title_artist_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.wav';self.audio(source)
            published=publish_music(source,root/'music','Faded',['Alan Walker'])
            self.assertEqual(published.name,'Alan Walker - Faded.wav')
            tags=WAVE(published).tags
            self.assertEqual(set(tags.keys()),{'TIT2','TPE1'})
            self.assertEqual(tags['TIT2'].text,['Faded']);self.assertEqual(tags['TPE1'].text,['Alan Walker'])
            self.assertFalse(list((root/'music').glob('*.part')))
    def test_concurrent_same_names_never_replace_existing_or_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'music';folder.mkdir()
            existing=folder/'Artist - Song.wav';existing.write_bytes(b'original user file')
            sources=[]
            for number in range(5):
                source=root/(str(number)+'.wav');self.audio(source);sources.append(source)
            with ThreadPoolExecutor(max_workers=5) as pool:
                paths=list(pool.map(lambda source:publish_music(source,folder,'Song',['Artist']),sources))
            self.assertEqual(len(set(paths)),5)
            self.assertEqual(existing.read_bytes(),b'original user file')
            self.assertEqual({path.name for path in paths},{f'Artist - Song ({number}).wav' for number in range(2,7)})
    def test_tagging_failure_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.wav';self.audio(source)
            with patch('music_files.write_music_tags',side_effect=ValueError('tagging failed')):
                with self.assertRaises(ValueError):publish_music(source,root/'music','Song',['Artist'])
            self.assertFalse(list((root/'music').iterdir()))


if __name__=='__main__':unittest.main()
