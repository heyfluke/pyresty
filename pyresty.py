#!/usr/bin/env python
#-*- coding: utf-8 -*-

import tkMessageBox
import restclient

try:
    # Python2
    import Tkinter as tk
except ImportError:
    # Python3
    import tkinter as tk

def center(win):
    win.update_idletasks()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = 768#win.winfo_width() + (frm_width*2)
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = 500#win.winfo_height() + (titlebar_height + frm_width)
    x = (win.winfo_screenwidth() / 2) - (win_width / 2)
    y = win.winfo_rooty() #(win.winfo_screenheight() / 2) - (win_height / 2)
    # geom = (win.winfo_width(), win.winfo_height(), x, y) # see note
    geom = (win_width, win_height, x, y) # see note
    win.geometry('{0}x{1}+{2}+{3}'.format(*geom))




class simpleapp_tk(tk.Tk):
    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        center(self)
        self.grid()

        self.entryVariable = tk.StringVar()
        self.entry = tk.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,row=0,columnspan=3,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)
        self.entryVariable.set(u"http://")

        get_button = tk.Button(self,text=u"GET", command=self.OnGETClicked)
        get_button.grid(column=3,row=0)

        self.labelVariable = tk.StringVar()
        label = tk.Label(self,textvariable=self.labelVariable,
                              anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=1,columnspan=4,sticky='EW')
        self.labelVariable.set(u"Hello !")

        save_button = tk.Button(self,text=u"保存配置", command=self.OnSaveConfigClicked)
        save_button.grid(column=0,row=2)

        clear_button = tk.Button(self,text=u"恢复默认", command=self.OnClearConfigClicked)
        clear_button.grid(column=2,row=2)

        self.header_key_list = []
        self.header_value_list = []
        ROW_BEFORE_OPTIONS = 3
        OPTION_COUNT = 5
        for i in range(OPTION_COUNT):
            OPTIONS = [
                "",
                'Connection', 
                'User-Agent', 
                'X-Requested-With',
                'Accept',
                'DNT',
                'Referer',
                'Accept-Encoding',
                'Accept-Language'
            ]

            variable = tk.StringVar(self)
            variable.set(OPTIONS[0]) # default value

            w = apply(tk.OptionMenu, (self, variable) + tuple(OPTIONS))
            w.grid(column=0, row=ROW_BEFORE_OPTIONS+i, columnspan=1, sticky='W')
            self.header_key_list.append(variable)
            
            value_variable = tk.StringVar()
            value_entry = tk.Entry(self,textvariable=value_variable)
            value_entry.grid(column=1, row=ROW_BEFORE_OPTIONS+i, columnspan=3, sticky='W')
            self.header_value_list.append(value_variable)

        self.msg = tk.Text(self, height=15, width=700)
        self.msg.grid(row=ROW_BEFORE_OPTIONS+OPTION_COUNT, columnspan=4)
        
        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,False)

        self.update()
        self.geometry(self.geometry())     

        self.entry.focus_set()
        # self.entry.selection_range(0, tk.END)

    def Main(self):
        self.title('PyRESTy HTTP Client')
        self.protocol("WM_DELETE_WINDOW", self.AskQuit)
        self.mainloop()

    def OnGETClicked(self):
        url = self.entryVariable.get()
        print 'url', url
        if len(url) < 8 or url.find('http://') != 0:
            tkMessageBox.showinfo("出错", "请输入http的url")
        else:
            headers = {}
            for i in range(len(self.header_key_list)):
                key = self.header_key_list[i]
                value = self.header_value_list[i]
                print 'header #%d: %s=%s' % (i, key.get(), value.get())
                if len(key.get()):
                    headers[key.get()] = value.get()
            ret = restclient.request('GET', url, headers=headers, ret_limit=40000)
            self.msg.insert(tk.END, ret)

    def OnSaveConfigClicked(self):
        pass

    def OnClearConfigClicked(self):
        pass

    def OnPressEnter(self,event):
        self.labelVariable.set( self.entryVariable.get()+" (You pressed ENTER)" )

    def AskQuit(self):
        # if tkMessageBox.askokcancel("退出", "确定退出吗?"):
        #     self.destroy()
        self.destroy()

if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.Main()
