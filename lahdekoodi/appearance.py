"""Dark desktop interface. Kept separate from download and update behavior."""
import ctypes
import os
import tkinter as tk
import customtkinter as ctk
from download_table import DownloadTable

BG='#080808'
PANEL='#121212'
FIELD='#202020'
TEXT='#f5f5f5'
MUTED='#989898'

class Combo(ctk.CTkComboBox):
    def current(self,index=None):
        values=self.cget('values')
        if index is not None:
            if 0<=index<len(values): self.set(values[index])
            return index
        try: return values.index(self.get())
        except ValueError: return -1
    def __setitem__(self,key,value): self.configure(**{key:value})

class SourceSwitch(ctk.CTkSegmentedButton):
    def configure(self,**kwargs):
        if kwargs.get('state')=='readonly': kwargs['state']='normal'
        return super().configure(**kwargs)

class Progress(ctk.CTkProgressBar):
    def start(self,interval=None):
        self.configure(mode='indeterminate'); super().start()
    def stop(self):
        super().stop(); self.configure(mode='determinate'); self.set(0)
    def show_fraction(self,value):
        super().stop(); self.configure(mode='determinate'); self.set(value)

class LinkInput(ctk.CTkTextbox):
    def get(self,index1='1.0',index2='end-1c'):
        return super().get(index1,index2)
    def set(self,value):
        self.delete('1.0','end')
        self.insert('1.0',value)

def dark_titlebar(window):
    if os.name!='nt': return
    try:
        handle=ctypes.windll.user32.GetParent(window.winfo_id())
        for attribute,value in [(20,1),(35,0x080808),(36,0xf5f5f5),(34,0x202020)]:
            color=ctypes.c_int(value)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(handle),attribute,ctypes.byref(color),ctypes.sizeof(color))
    except (AttributeError,OSError): pass

def build_interface(app,settings,preview=False):
    ctk.set_appearance_mode('dark')
    app.configure(fg_color=BG)
    app.primary_buttons=[]; app.secondary_buttons=[]; app.dark_combos=[]
    def frame(parent,**kwargs): return ctk.CTkFrame(parent,fg_color='transparent',**kwargs)
    def label(parent,text='',**kwargs):
        options={'text':text,'font':('Segoe UI',12),'text_color':MUTED,'anchor':'w'}; options.update(kwargs)
        return ctk.CTkLabel(parent,**options)
    def button(parent,text,command,primary=False,**kwargs):
        options={'text':text,'command':command,'height':38,'corner_radius':15,'font':('Segoe UI',12,'bold'),
                 'text_color_disabled':'#626262','fg_color':'#242424','hover_color':'#333333','text_color':TEXT}
        options.update(kwargs); control=ctk.CTkButton(parent,**options)
        (app.primary_buttons if primary else app.secondary_buttons).append(control)
        return control
    def entry(parent,variable,placeholder='',**kwargs):
        return ctk.CTkEntry(parent,textvariable=variable,placeholder_text=placeholder,height=40,corner_radius=11,
                            fg_color=FIELD,border_color='#303030',border_width=1,text_color=TEXT,
                            placeholder_text_color='#777777',font=('Segoe UI',13),**kwargs)
    def combo(parent,variable,values,width=180):
        widget=Combo(parent,variable=variable,values=values,width=width,height=36,corner_radius=10,
                     fg_color=FIELD,border_color='#303030',button_color='#303030',button_hover_color='#414141',
                     text_color=TEXT,dropdown_fg_color='#242424',dropdown_text_color=TEXT,
                     dropdown_hover_color='#353535',font=('Segoe UI',12),dropdown_font=('Segoe UI',12),state='readonly')
        app.dark_combos.append(widget); return widget

    outer=frame(app); outer.pack(fill='both',expand=True,padx=24,pady=(16,20))
    header=frame(outer); header.pack(fill='x')
    brand=frame(header); brand.pack(side='left')
    label(brand,'Albumilataaja',font=('Segoe UI',27,'bold'),text_color=TEXT).pack(anchor='w')
    label(brand,'Oma musiikkikirjastosi',font=('Segoe UI',12)).pack(anchor='w')
    app.update_button=button(header,'Tarkista päivitykset',lambda:app.check_updates(True),width=166)
    app.update_button.pack(side='right')
    app.tools_update_button=button(header,'Työkalujen päivitykset',app.open_tools,width=178)
    app.tools_update_button.pack(side='right',padx=(8,10))
    if preview: label(header,'ESIKATSELU',font=('Segoe UI',10,'bold'),fg_color='#202020',corner_radius=9,width=100,height=28,anchor='center').pack(side='right',padx=12)

    sources=frame(outer); sources.pack(fill='x',pady=(16,12))
    label(sources,'Lähde',width=54).pack(side='left')
    app.source_display=tk.StringVar(value='Spotify' if app.source.get()=='Spotify (spotDL)' else 'YouTube')
    def switch(value):
        app.source.set('Spotify (spotDL)' if value=='Spotify' else 'YouTube'); app.source_switched()
    app.source_combo=SourceSwitch(sources,values=['YouTube','Spotify'],variable=app.source_display,command=switch,
        height=38,width=285,corner_radius=13,font=('Segoe UI',13,'bold'),fg_color='#1b1b1b',unselected_color='#1b1b1b',unselected_hover_color='#292929')
    app.source_combo.pack(side='left')
    app.source_note=label(sources); app.source_note.pack(side='left',padx=18)

    session=frame(outer); session.pack(fill='x',pady=(0,8))
    app.cookie_label=label(session,'YouTube-istunto: valittu tiedosto' if app.cookie_file.get() else 'YouTube-istunto: ei käytössä',font=('Segoe UI',11))
    app.cookie_label.pack(side='left')
    label(session,'Latauksia kerralla',font=('Segoe UI',11)).pack(side='left',padx=(18,8))
    app.parallel_combo=combo(session,app.parallel,['1','2','3','4','5','15','20'],width=68)
    app.parallel_combo.pack(side='left')
    button(session,'YouTube-evästeet',app.choose_youtube_cookies,width=145,height=28,font=('Segoe UI',11)).pack(side='right')
    button(session,'Poista valinta',app.clear_youtube_cookies,width=110,height=28,font=('Segoe UI',11)).pack(side='right',padx=8)

    link=frame(outer); link.pack(fill='x')
    app.direct=LinkInput(link,height=76,corner_radius=11,fg_color=FIELD,border_color='#303030',border_width=1,
                        text_color=TEXT,font=('Segoe UI',13),wrap='none',activate_scrollbars=False)
    app.direct.pack(side='left',fill='x',expand=True)
    app.link_btn=button(link,'Lataa linkit',app.download_link,True,width=150,height=40); app.link_btn.pack(side='left',padx=(10,0))
    app.link_note=label(outer,font=('Segoe UI',10),height=18); app.link_note.pack(anchor='w',pady=(2,5))

    path=frame(outer); path.pack(fill='x',pady=(0,9))
    label(path,'Tallennuskansio',width=114).pack(side='left')
    entry(path,app.destination).pack(side='left',fill='x',expand=True)
    button(path,'Valitse…',app.choose_folder,width=94).pack(side='left',padx=(8,0))
    button(path,'Avaa kansio',app.open_folder,width=114).pack(side='left',padx=(8,0))

    actions=frame(outer); actions.pack(fill='x')
    label(actions,'Muoto',width=52).pack(side='left')
    combo(actions,app.format,['flac','opus','mp3','m4a'],width=94).pack(side='left')
    label(actions,'Kansiomuoto',width=100).pack(side='left',padx=(18,0))
    combo(actions,app.layout,['Albumi, Vuosi','Vuosi - Albumi','Suoraan tallennuskansioon'],width=210).pack(side='left')
    app.stop_btn=button(actions,'Keskeytä',app.stop,width=104,height=40,state='disabled')
    app.stop_btn.pack(side='right')
    label(outer,'YouTuben äänen tallentaminen FLACiksi ei paranna alkuperäistä äänenlaatua.',font=('Segoe UI',10),text_color='#717171',height=18).pack(anchor='w',pady=(5,0))
    app.download_panel=ctk.CTkFrame(outer,fg_color=PANEL,corner_radius=16,border_width=1,border_color='#242424')
    app.download_panel.pack(fill='both',expand=True,pady=(12,6))
    bar=frame(app.download_panel);bar.pack(fill='x',padx=16,pady=(10,8))
    label(bar,'Lataukset',font=('Segoe UI',18,'bold'),text_color=TEXT).pack(side='left')
    label(bar,'Kaksoisnapsauta riviä nähdäksesi tiedot',font=('Segoe UI',11)).pack(side='left',padx=16)
    app.download_table=DownloadTable(app.download_panel,app.download_rows)
    app.download_table.pack(fill='both',expand=True,padx=12,pady=(0,12))
    app.progress=Progress(outer,mode='determinate',height=4,corner_radius=2,fg_color='#242424'); app.progress.set(0)
    app.progress.pack(fill='x',pady=(7,5))
    label(outer,textvariable=app.queue_summary,text_color='#d0d0d0',font=('Segoe UI',11),height=20).pack(anchor='w')
    label(outer,textvariable=app.status,wraplength=1040,text_color='#bdbdbd',font=('Segoe UI',11),height=20).pack(anchor='w')
    log_header=frame(outer); log_header.pack(fill='x',pady=(3,4))
    label(log_header,'Tarkempi latausloki',font=('Segoe UI',11)).pack(side='left')
    app.console_visible=True
    app.console_button=button(log_header,'Piilota loki',app.toggle_console,width=128,height=27,font=('Segoe UI',11))
    app.console_button.pack(side='right')
    app.log_frame=ctk.CTkFrame(outer,fg_color='#101010',corner_radius=12); app.log_frame.pack(fill='x')
    app.log=tk.Text(app.log_frame,height=6,bg='#101010',fg='#bbbbbb',insertbackground=TEXT,font=('Consolas',10),
                    relief='flat',highlightthickness=0,state='disabled',wrap='word',padx=12,pady=8)
    app.log.pack(fill='both',expand=True,padx=3,pady=3)
    if not settings.get('show_details',False): app.toggle_console()
    app.after(200,lambda:dark_titlebar(app))

def apply_theme(app):
    spotify=app.source.get()=='Spotify (spotDL)'
    accent,hover,tint,soft,border=('#1ed760','#36e778','#123120','#1d402b','#21402e') if spotify else ('#e83b46','#fa505b','#301619','#482027','#432126')
    for control in app.primary_buttons:
        control.configure(fg_color='#242424' if control.cget('state')=='disabled' else accent,hover_color=hover,text_color='#08150d' if spotify else '#ffffff')
    for control in app.secondary_buttons: control.configure(fg_color=tint,hover_color=soft,text_color='#e2e2e2')
    for control in app.dark_combos: control.configure(button_hover_color=soft,dropdown_hover_color=soft)
    app.source_combo.configure(selected_color=accent,selected_hover_color=hover,text_color=TEXT)
    for control in app.source_combo.winfo_children():
        if isinstance(control,ctk.CTkButton): control.configure(text_color='#08150d' if spotify and control.cget('text')=='Spotify' else TEXT)
    app.source_combo.configure(text_color_disabled='#777777')
    app.progress.configure(progress_color=accent if app.busy or app.queue_tracker.total else '#242424')
    app.download_panel.configure(border_color=border)
