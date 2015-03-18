#!/usr/bin/env python
#-*- coding: utf-8 -*-

import tkMessageBox
import restclient
import cPickle as pickle

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

CURRENT_CONFIG_VERSION = 0


class Config(object):
    def __init__(self):
        super(Config, self).__init__()
        global CURRENT_CONFIG_VERSION
        self.config_version = CURRENT_CONFIG_VERSION
        self.url = 'http://'
        self.headers = {}
        self.max_recv = 1024 * 10
    def getConfigVersion(self):
        return self.config_version
    def setUrl(self, url):
        self.url = url
    def getUrl(self):
        return self.url
    def getHeaders(self):
        return self.headers
    def setMaxRecv(self, max_recv):
        self.max_recv = max_recv
    def getMaxRecv(self):
        return self.max_recv


class PyRESTyApp(tk.Tk):
    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.CONFIG_FILE = 'config.conf'
        self.initialize()

    def loadConfig(self):
        global CURRENT_CONFIG_VERSION
        # FIXME: relative path
        try:
            f = open(self.CONFIG_FILE, 'rb')
            self.config = pickle.load(f)
            f.close()
            try:
                if self.config.getConfigVersion() != CURRENT_CONFIG_VERSION:
                    print 'config version not match'
                    self.config = Config()
            except AttributeError:
                print 'AttributeError'
                self.config = Config()
        except IOError:
            print 'no config.conf found'
            self.config = Config()

    def saveConfig(self):
        try:
            f = open(self.CONFIG_FILE, 'wb')
            pickle.dump(self.config, f)
            f.close()
            return True
        except IOError:
            print 'dump config.conf failed'
            return False

    def initialize(self):
        self.loadConfig()

        center(self)
        self.grid()

        self.entryVariable = tk.StringVar()
        self.entry = tk.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,row=0,columnspan=3,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)
        self.entryVariable.set(self.config.getUrl())

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
        clear_button.grid(column=1,row=2)

        max_recv_label_variable = tk.StringVar()
        max_recv_label = tk.Label(self,textvariable=max_recv_label_variable,
                              anchor="w")
        max_recv_label.grid(column=2,row=2,sticky='EW')
        max_recv_label_variable.set(u'最大TCP接收量:')

        self.max_recv_entry_variable = tk.StringVar()
        self.max_recv_entry = tk.Entry(self,textvariable=self.max_recv_entry_variable)
        self.max_recv_entry.grid(column=3,row=2,columnspan=3,sticky='EW')
        self.max_recv_entry_variable.set(self.config.getMaxRecv())

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

            def key_change(*args):
                print 'change for key#%d args %s' % (i, str(args))
            key_variable = tk.StringVar(self)
            key_variable.set(OPTIONS[0]) # default value
            key_variable.trace('w', key_change)

            w = apply(tk.OptionMenu, (self, key_variable) + tuple(OPTIONS))
            w.grid(column=0, row=ROW_BEFORE_OPTIONS+i, columnspan=1, sticky='W')
            self.header_key_list.append(key_variable)
            
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
            ret = restclient.request('GET', url, headers=headers, ret_limit=self.config.getMaxRecv())
            self.msg.insert(tk.END, ret)

    def OnSaveConfigClicked(self):
        url = self.entryVariable.get()
        self.config.setUrl(url)
        if not self.saveConfig():
            tkMessageBox.showinfo("出错", "保存错误")

    def OnClearConfigClicked(self):
        url = self.entryVariable.get()
        self.config = Config()
        if not self.saveConfig():
            tkMessageBox.showinfo("出错", "清除错误")

    def OnPressEnter(self,event):
        self.labelVariable.set( self.entryVariable.get()+" (You pressed ENTER)" )

    def AskQuit(self):
        # if tkMessageBox.askokcancel("退出", "确定退出吗?"):
        #     self.destroy()
        self.destroy()

if __name__ == "__main__":
    app = PyRESTyApp(None)
    app.Main()
