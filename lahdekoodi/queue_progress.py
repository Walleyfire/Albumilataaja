"""Whole-queue progress and a deliberately approximate remaining-time estimate."""
import json
import math
import re
import threading
import time

PROGRESS='__ALBUMILATAAJA_PROGRESS__'
TRACK_DONE='__ALBUMILATAAJA_TRACK_DONE__'

def approximate_time(seconds):
    if seconds<60: return 'alle minuutti'
    minutes=max(1,round(seconds/60))
    if minutes<60: return f'noin {minutes} min'
    hours,minutes=divmod(minutes,60)
    return f'noin {hours} h'+(f' {minutes} min' if minutes else '')

class QueueProgress:
    def __init__(self,clock=time.monotonic):
        self.clock=clock; self.lock=threading.RLock(); self.reset()
    def reset(self):
        with self.lock:
            self.total=0; self.completed=0; self.failed=0; self.index=0
            self.fraction=0.; self.started=None; self.ended=None; self.active=False; self.cancelled=False
    def begin(self,total):
        with self.lock:
            self.reset(); self.total=max(0,int(total)); self.started=self.clock(); self.active=self.total>0
    def start_task(self,index):
        with self.lock:
            self.index=index; self.fraction=0.
    def update(self,fraction):
        with self.lock:
            if self.active and math.isfinite(fraction): self.fraction=max(self.fraction,min(1.,max(0.,fraction)))
    def finish_task(self,index,failed=False):
        with self.lock:
            self.completed=max(self.completed,index+1); self.failed+=bool(failed); self.fraction=0.; self.index=self.completed
            if self.completed>=self.total: self.active=False; self.ended=self.clock()
    def stop(self,cancelled=False):
        with self.lock:
            if self.active: self.active=False; self.ended=self.clock(); self.cancelled=cancelled
    def consume(self,line):
        if line.startswith((PROGRESS,TRACK_DONE)):
            try:
                prefix=TRACK_DONE if line.startswith(TRACK_DONE) else PROGRESS
                data=json.loads(line[len(prefix):])
                count=max(1,int(data.get('count') or 1)); index=max(1,int(data.get('index') or 1))
                if prefix==TRACK_DONE: fraction=index/count
                else:
                    total=float(data.get('total') or 0); downloaded=float(data.get('downloaded') or 0)
                    media_fraction=min(1.,downloaded/total) if total>0 else 0.
                    fraction=(index-1+.9*media_fraction)/count
                self.update(fraction)
            except (ValueError,TypeError,ZeroDivisionError): pass
            return True
        match=re.search(r'\b(\d+)\s*/\s*(\d+)\s+complete\b',line,re.I)
        if match and int(match[2])>0: self.update(int(match[1])/int(match[2]))
        return False
    def snapshot(self):
        with self.lock:
            if not self.total: return None
            fraction=min(1.,(self.completed+self.fraction)/self.total)
            elapsed=max(0.,(self.ended if self.ended is not None else self.clock())-self.started)
            complete=self.completed>=self.total
            percent=100 if complete else min(99,int(fraction*100))
            summary=f'Koko jono · {percent} % · {self.completed}/{self.total} julkaisua'
            eta=None
            if complete: summary+=' · '+('käsitelty, tarkista lokin virheet' if self.failed else 'valmis')
            elif not self.active: summary+=' · '+('keskeytetty' if self.cancelled else 'pysäytetty')
            elif fraction>0 and elapsed>=3:
                # Publications have different sizes. This estimate uses the
                # observed overall pace, including search/conversion time.
                eta=elapsed*(1-fraction)/fraction
                summary+=' · '+approximate_time(eta)+' jäljellä'
            else: summary+=' · lasketaan aika-arviota…'
            return {'fraction':fraction,'percent':percent,'text':summary,'eta_seconds':eta,'active':self.active}
