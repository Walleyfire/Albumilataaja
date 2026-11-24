"""Dark, scrollable file table with progress fills and a separate error column."""
import tkinter as tk
from tkinter import font,messagebox
import customtkinter as ctk
from download_rows import STAGES


class DownloadTable(ctk.CTkFrame):
    def __init__(self,parent,model):
        super().__init__(parent,fg_color='#121212',corner_radius=0,height=80)
        self.model=model; self.row_height=43
        self.main_font=font.Font(family='Segoe UI',size=10)
        self.small_font=font.Font(family='Segoe UI',size=9)
        self.header=tk.Canvas(self,height=27,bg='#1c1c1c',highlightthickness=0)
        self.header.pack(fill='x')
        self.body=tk.Canvas(self,bg='#121212',highlightthickness=0,height=50)
        self.body.pack(fill='both',expand=True)
        self.body.bind('<Configure>',lambda event:self.render())
        self.body.bind('<MouseWheel>',self.wheel)
        self.body.bind('<Double-Button-1>',self.details)
    def wheel(self,event):
        self.body.yview_scroll(-int(event.delta/120),'units');self.render();return 'break'
    def clipped(self,text,width,small=False):
        face=self.small_font if small else self.main_font
        if face.measure(text)<=width: return text
        low,high=0,len(text)
        while low<high:
            middle=(low+high+1)//2
            if face.measure(text[:middle]+'…')<=width:low=middle
            else:high=middle-1
        return text[:low]+'…' if low else ''
    def render(self):
        width=max(1,self.body.winfo_width()); height=max(1,self.body.winfo_height())
        columns=[int(width*x) for x in (0,.04,.35,.54,.64,.80,1)]
        self.header.delete('all')
        for i,title in enumerate(['#','KAPPALE / ARTISTI','ALBUMI','LÄHDE','TILA','VIRHE']):
            self.header.create_text(columns[i]+8,14,text=title,fill='#9a9a9a',anchor='w',font=self.small_font)
        rows=list(self.model.rows.values())
        self.body.configure(scrollregion=(0,0,width,max(height,len(rows)*self.row_height)),yscrollincrement=self.row_height)
        top=max(0,int(self.body.canvasy(0)//self.row_height));bottom=min(len(rows),top+height//self.row_height+2)
        self.body.delete('all')
        if not rows:
            self.body.create_text(width/2,height/2,text='Kappaleiden tilat näkyvät tässä latauksen aikana.',fill='#888888',font=self.main_font)
        for index in range(top,bottom):
            row=rows[index];y=index*self.row_height;stage=row['stage']
            base='#161616' if index%2==0 else '#121212'
            self.body.create_rectangle(0,y,width,y+self.row_height,fill=base,outline='')
            percentage=row['percent'] or (90 if stage=='converting' else 0)
            color='#183b29' if row['source']=='Spotify' else '#371c21'
            if stage in ('done','skipped'): color='#183a28'
            if stage=='error': color='#361c21'
            if percentage:
                self.body.create_rectangle(0,y,columns[5]*percentage/100,y+self.row_height,fill=color,outline='')
            if row['error']:
                self.body.create_rectangle(columns[5],y,width,y+self.row_height,fill='#28171b',outline='')
            self.body.create_line(0,y+self.row_height-1,width,y+self.row_height-1,fill='#242424')
            self.body.create_text(8,y+20,text=str(index+1),fill='#999999',anchor='w',font=self.small_font)
            title_width=columns[2]-columns[1]-16
            self.body.create_text(columns[1]+8,y+13,text=self.clipped(row['title'],title_width),fill='#f0f0f0',anchor='w',font=self.main_font)
            self.body.create_text(columns[1]+8,y+31,text=self.clipped(row['artist'],title_width,True),fill='#aaaaaa',anchor='w',font=self.small_font)
            self.body.create_text(columns[2]+8,y+20,text=self.clipped(row['album'],columns[3]-columns[2]-16),fill='#c4c4c4',anchor='w',font=self.main_font)
            source_color='#1ed760' if row['source']=='Spotify' else '#f34b56'
            self.body.create_oval(columns[3]+8,y+17,columns[3]+15,y+24,fill=source_color,outline='')
            self.body.create_text(columns[3]+21,y+20,text=row['source'],fill='#bdbdbd',anchor='w',font=self.small_font)
            status=STAGES[stage]
            if stage=='downloading' and row['percent'] is not None: status+=f" · {int(row['percent'])} %"
            self.body.create_text(columns[4]+8,y+20,text=self.clipped(status,columns[5]-columns[4]-16),fill='#ff9098' if stage=='error' else '#dedede',anchor='w',font=self.main_font)
            self.body.create_text(columns[5]+8,y+20,text=self.clipped(row['error'],width-columns[5]-16),fill='#ff8b96',anchor='w',font=self.small_font)
    def details(self,event):
        rows=list(self.model.rows.values());index=int(self.body.canvasy(event.y)//self.row_height)
        if not 0<=index<len(rows): return
        row=rows[index]
        text=f"{row['artist']} – {row['title']}\n{row['album']}\n\nTila: {STAGES[row['stage']]}"
        if row['filename']: text+='\n\nTiedosto: '+row['filename']
        if row['error']: text+='\n\nVirhe: '+row['error']
        messagebox.showinfo('Latauksen tiedot',text,parent=self.winfo_toplevel())
