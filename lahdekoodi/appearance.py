"""Dark desktop interface. Kept separate from download and update behavior."""
import ctypes
import os
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

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

    artist_panel=ctk.CTkFrame(outer,fg_color=PANEL,corner_radius=16); artist_panel.pack(fill='x')
    search=frame(artist_panel); search.pack(fill='x',padx=14,pady=(12,8))
    app.search_entry=entry(search,app.query,'Kirjoita artistin nimi'); app.search_entry.pack(side='left',fill='x',expand=True)
    app.search_entry.bind('<Return>',lambda event:app.search())
    app.search_btn=button(search,'Hae artisti',app.search,True,width=150,height=40); app.search_btn.pack(side='left',padx=(10,0))
    choose=frame(artist_panel); choose.pack(fill='x',padx=14,pady=(0,12))
    app.combo=combo(choose,app.artist_choice,[],width=400); app.combo.pack(side='left',fill='x',expand=True)
    app.singles_control=ctk.CTkCheckBox(choose,text='Singlet ja EP:t',variable=app.singles,font=('Segoe UI',12),
                                    text_color='#bdbdbd',width=128,checkbox_width=18,checkbox_height=18,corner_radius=5,border_width=2)
    app.singles_control.pack(side='left',padx=16)
    app.album_btn=button(choose,'Näytä julkaisut',app.load_albums,width=150,height=36); app.album_btn.pack(side='left')

    app.album_panel=ctk.CTkFrame(outer,fg_color=PANEL,corner_radius=16,border_width=1,border_color='#242424')
    app.album_panel.pack(fill='both',expand=True,pady=(12,10))
    bar=frame(app.album_panel); bar.pack(fill='x',padx=16,pady=(10,8))
    label(bar,'Julkaisut',font=('Segoe UI',18,'bold'),text_color=TEXT).pack(side='left')
    label(bar,'Uusimmat ensin',font=('Segoe UI',11)).pack(side='left',padx=14)
    button(bar,'Valitse kaikki',lambda:app.tree.selection_set(app.tree.get_children()),width=118,height=30).pack(side='right')
    tree_frame=tk.Frame(app.album_panel,bg=PANEL,bd=0,highlightthickness=0); tree_frame.pack(fill='both',expand=True,padx=12,pady=(0,12))
    app.table_style=ttk.Style(app); app.table_style.theme_use('clam')
    app.table_style.configure('Albums.Treeview',background=PANEL,fieldbackground=PANEL,foreground='#e5e5e5',
                             rowheight=34,borderwidth=0,relief='flat',font=('Segoe UI',11))
    app.table_style.configure('Albums.Treeview.Heading',background='#1c1c1c',foreground='#a6a6a6',font=('Segoe UI',10),
                             padding=(10,7),borderwidth=0,relief='flat')
    app.table_style.layout('Albums.Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
    app.table_style.map('Albums.Treeview.Heading',background=[('active','#282828')])
    app.tree=ttk.Treeview(tree_frame,columns=('title','year','kind'),show='headings',selectmode='extended',height=4,style='Albums.Treeview')
    for key,text,width,stretch in [('title','ALBUMI / JULKAISU',640,True),('year','VUOSI',90,False),('kind','TYYPPI',145,False)]:
        app.tree.heading(key,text=text,anchor='w'); app.tree.column(key,width=width,minwidth=width if not stretch else 220,stretch=stretch,anchor='w')
    app.tree.pack(fill='both',expand=True)
    app.tree.tag_configure('even',background='#151515'); app.tree.tag_configure('odd',background='#121212')
    app.empty_label=label(tree_frame,'Hae artisti nähdäksesi julkaisut',font=('Segoe UI',14),text_color='#777777',fg_color=PANEL,anchor='center')
    app.empty_label.place(relx=.5,rely=.55,anchor='center')

    link=frame(outer); link.pack(fill='x')
    entry(link,app.direct,'Liitä albumin, soittolistan tai kappaleen linkki').pack(side='left',fill='x',expand=True)
    app.link_btn=button(link,'Lataa linkistä',app.download_link,width=150,height=40); app.link_btn.pack(side='left',padx=(10,0))
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
    combo(actions,app.layout,['Albumi, Vuosi','Vuosi - Albumi'],width=160).pack(side='left')
    app.download_btn=button(actions,'↓  Lataa valitut julkaisut',app.download_selected,True,width=228,height=40)
    app.stop_btn=button(actions,'Keskeytä',app.stop,width=104,height=40,state='disabled')
    app.stop_btn.pack(side='right'); app.download_btn.pack(side='right',padx=(8,10))
    label(outer,'YouTuben äänen tallentaminen FLACiksi ei paranna alkuperäistä äänenlaatua.',font=('Segoe UI',10),text_color='#717171',height=18).pack(anchor='w',pady=(5,0))
    app.progress=Progress(outer,mode='determinate',height=4,corner_radius=2,fg_color='#242424'); app.progress.set(0)
    app.progress.pack(fill='x',pady=(7,5))
    label(outer,textvariable=app.queue_summary,text_color='#d0d0d0',font=('Segoe UI',11),height=20).pack(anchor='w')
    label(outer,textvariable=app.status,wraplength=1040,text_color='#bdbdbd',font=('Segoe UI',11),height=20).pack(anchor='w')
    log_header=frame(outer); log_header.pack(fill='x',pady=(3,4))
    label(log_header,'Latausloki',font=('Segoe UI',11)).pack(side='left')
    app.console_visible=True
    app.console_button=button(log_header,'Piilota console',app.toggle_console,width=128,height=27,font=('Segoe UI',11))
    app.console_button.pack(side='right')
    app.log_frame=ctk.CTkFrame(outer,fg_color='#101010',corner_radius=12); app.log_frame.pack(fill='x')
    app.log=tk.Text(app.log_frame,height=6,bg='#101010',fg='#bbbbbb',insertbackground=TEXT,font=('Consolas',10),
                    relief='flat',highlightthickness=0,state='disabled',wrap='word',padx=12,pady=8)
    app.log.pack(fill='both',expand=True,padx=3,pady=3)
    if not settings.get('show_console',True): app.toggle_console()
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
    app.singles_control.configure(fg_color=accent,hover_color=hover,border_color='#616161',checkmark_color='#08150d' if spotify else '#ffffff')
    app.progress.configure(progress_color=accent if app.busy or app.queue_tracker.total else '#242424')
    app.album_panel.configure(border_color=border)
    app.table_style.map('Albums.Treeview',background=[('selected',soft)],foreground=[('selected','#ffffff')])
