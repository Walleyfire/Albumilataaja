import tkinter as tk
import customtkinter as ctk


class ToolDialog(ctk.CTkToplevel):
    def __init__(self,app):
        super().__init__(app);self.app=app;self.rows=[];self.choices={}
        self.title('Työkalujen päivitykset');self.geometry('900x480');self.resizable(False,False)
        self.configure(fg_color='#101010');self.transient(app)
        try:self.iconbitmap(app.iconbitmap())
        except tk.TclError:pass
        self.accent='#1ed760' if app.source.get()=='Spotify (spotDL)' else '#e83b46'
        self.button_text='#08150d' if app.source.get()=='Spotify (spotDL)' else '#ffffff'
        ctk.CTkLabel(self,text='Työkalujen päivitykset',font=('Segoe UI',23,'bold')).pack(anchor='w',padx=22,pady=(18,5))
        ctk.CTkLabel(self,text='Tarkistus virallisista GitHub-julkaisuista. Päivitykset asennetaan valitsemalla Päivitä valitut.',text_color='#aaaaaa').pack(anchor='w',padx=22)
        self.list=ctk.CTkFrame(self,fg_color='#191919',corner_radius=12);self.list.pack(fill='x',padx=20,pady=15)
        self.message=ctk.CTkLabel(self,text='Tarkistetaan…',wraplength=825,justify='left',anchor='w',text_color='#bbbbbb',height=48)
        self.message.pack(fill='x',padx=22)
        actions=ctk.CTkFrame(self,fg_color='transparent');actions.pack(fill='x',padx=22,pady=12)
        self.check=ctk.CTkButton(actions,text='Tarkista uudelleen',command=lambda:app.check_tools(self),width=155,fg_color=self.accent,text_color=self.button_text,corner_radius=12)
        self.check.pack(side='left')
        self.install=ctk.CTkButton(actions,text='Päivitä valitut',command=lambda:app.install_tools(self),width=155,fg_color=self.accent,text_color=self.button_text,corner_radius=12)
        self.install.pack(side='left',padx=10)
        ctk.CTkButton(actions,text='Sovelluspäivitys',command=lambda:app.check_updates(True),width=155,fg_color='#333333').pack(side='left')
        ctk.CTkButton(actions,text='Sulje',command=self.destroy,width=90,fg_color='#333333').pack(side='right')
        app.check_tools(self)
    def checking(self):
        self.check.configure(state='disabled');self.install.configure(state='disabled');self.message.configure(text='Tarkistetaan uusimmat GitHub-julkaisut…')
    def show_versions(self,rows):
        self.rows=rows;self.choices={}
        for child in self.list.winfo_children():child.destroy()
        for column,(title,width) in enumerate([('TYÖKALU',170),('ASENNETTU',200),('SAATAVILLA',200),('TILA',205)]):
            ctk.CTkLabel(self.list,text=title,width=width,anchor='w',text_color='#888888',font=('Segoe UI',10)).grid(row=0,column=column,padx=(8,0),pady=(8,3))
        for number,row in enumerate(rows,1):
            choice=tk.BooleanVar(value=row['can_update']);self.choices[row['key']]=choice
            ctk.CTkCheckBox(self.list,text=row['name'],variable=choice,width=170,font=('Segoe UI',12),fg_color=self.accent,state='normal' if row['can_update'] else 'disabled').grid(row=number,column=0,padx=8,pady=9)
            for column,value in [(1,row['current']),(2,row['latest'] or '—')]:
                ctk.CTkLabel(self.list,text=value,width=200,anchor='w',font=('Segoe UI',11)).grid(row=number,column=column,padx=(8,0))
            state='Sovelluspäivityksen mukana' if row['managed'] and row['available'] else ('Päivitys saatavilla' if row['available'] else 'Ajan tasalla')
            if row['error']:state='Tarkistus epäonnistui'
            ctk.CTkLabel(self.list,text=state,width=205,anchor='w',text_color='#f19999' if row['error'] else '#9cd5ad',font=('Segoe UI',11)).grid(row=number,column=3,padx=(8,0))
        self.check.configure(state='normal');self.install.configure(state='normal' if any(r['can_update'] for r in rows) else 'disabled')
        errors=[row['name']+': '+row['error'] for row in rows if row['error']]
        self.message.configure(text='\n'.join(errors)[:700] if errors else 'yt-dlp, Deno ja FFmpeg voidaan päivittää suoraan. Mukautettu SpotDL päivitetään Albumilataajan mukana.')
    def selected(self):return [row for row in self.rows if row['can_update'] and self.choices[row['key']].get()]
