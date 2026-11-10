import unittest
from queue_progress import QueueProgress, PROGRESS, TRACK_DONE

class QueueProgressTests(unittest.TestCase):
    def setUp(self):
        self.now=0.; self.queue=QueueProgress(clock=lambda:self.now)
    def test_eta_includes_all_remaining_publications(self):
        self.queue.begin(4); self.queue.start_task(0); self.now=30.; self.queue.update(.5)
        snapshot=self.queue.snapshot()
        self.assertAlmostEqual(snapshot['fraction'],.125)
        self.assertAlmostEqual(snapshot['eta_seconds'],210.)
        self.assertIn('0/4 julkaisua',snapshot['text'])
        self.queue.finish_task(0); self.queue.start_task(1); self.now=60
        self.assertAlmostEqual(self.queue.snapshot()['eta_seconds'],180.)
    def test_youtube_conversion_and_retries_do_not_rewind(self):
        self.queue.begin(1)
        self.queue.consume(PROGRESS+'{"index":2,"count":4,"downloaded":100,"total":100}')
        first=self.queue.snapshot()['fraction']; self.assertLess(first,.5)
        self.queue.consume(PROGRESS+'{"index":2,"count":4,"downloaded":10,"total":100}')
        self.assertEqual(self.queue.snapshot()['fraction'],first)
        self.queue.consume(TRACK_DONE+'{"index":2,"count":4}')
        self.assertEqual(self.queue.snapshot()['fraction'],.5)
    def test_spotify_counter_and_cancellation(self):
        self.queue.begin(2); self.queue.consume('3/6 complete')
        self.assertEqual(self.queue.snapshot()['fraction'],.25)
        self.queue.stop(cancelled=True); self.now=500
        snapshot=self.queue.snapshot()
        self.assertIn('keskeytetty',snapshot['text']); self.assertIsNone(snapshot['eta_seconds'])
        self.assertLess(snapshot['percent'],100)
    def test_completion_errors_and_unknown_start(self):
        self.queue.begin(1)
        self.assertIsNone(self.queue.snapshot()['eta_seconds'])
        self.queue.consume(PROGRESS+'not-json')
        self.queue.finish_task(0,failed=True)
        self.assertEqual(self.queue.snapshot()['percent'],100)
        self.assertIn('tarkista lokin virheet',self.queue.snapshot()['text'])

if __name__=='__main__': unittest.main()
