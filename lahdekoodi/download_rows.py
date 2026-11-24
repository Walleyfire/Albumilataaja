"""Structured file status shared by the desktop UI and download workers."""
import json
import math

ROW_EVENT='__ALBUMILATAAJA_FILE__'
STAGES={'queued':'Jonossa','searching':'Etsitään ääntä','downloading':'Ladataan',
        'converting':'Muunnetaan','done':'Valmis','skipped':'Ohitettu',
        'error':'Virhe','cancelled':'Keskeytetty'}
TERMINAL={'done','skipped','error','cancelled'}


def row_event(emit,key,**values):
    emit(ROW_EVENT+json.dumps(dict(values,id=str(key)),ensure_ascii=False))


def parse_row(line):
    if not line.startswith(ROW_EVENT): return None
    try:
        data=json.loads(line[len(ROW_EVENT):])
        if isinstance(data,dict) and isinstance(data.get('id'),str) and data['id']: return data
    except (ValueError,TypeError): pass
    return {}


class DownloadRows:
    def __init__(self): self.rows={}
    def clear(self): self.rows.clear()
    def update(self,data):
        key=data.get('id')
        if not isinstance(key,str) or not key or len(key)>4096: return
        row=self.rows.setdefault(key,{'id':key,'title':'Kappale','artist':'','album':'','source':'YouTube',
                                     'stage':'queued','percent':None,'error':'','filename':''})
        stage=data.get('stage',row['stage'])
        if stage not in STAGES: stage=row['stage']
        if row['stage'] in TERMINAL and stage not in TERMINAL: return
        row['stage']=stage
        for field in ('title','artist','album','source','error','filename'):
            if field in data and data[field] is not None:
                row[field]=' '.join(str(data[field]).split())[:4096 if field=='filename' else 2000]
        if data.get('percent') is not None:
            try:
                percent=float(data['percent'])
                if math.isfinite(percent): row['percent']=max(row['percent'] or 0,min(100,max(0,percent)))
            except (ValueError,TypeError): pass
        if stage in ('done','skipped'): row['percent']=100; row['error']=''
    def finish(self,cancelled=False,error=''):
        for row in self.rows.values():
            if row['stage'] not in TERMINAL:
                row['stage']='cancelled' if cancelled else 'error'
                row['error']=error or ('' if cancelled else 'Tiedoston valmistumista ei voitu vahvistaa. Katso tarkempi loki.')
