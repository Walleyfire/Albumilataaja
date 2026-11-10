"""Local appearance preview; never checks or installs published updates."""
import os
os.environ['ALBUMILATAAJA_PREVIEW']='1'
from app import App

if __name__=='__main__': App().mainloop()
