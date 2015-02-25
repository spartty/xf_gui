#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from Tkinter import *
from PIL import Image, ImageTk
from tkMessageBox import showerror,showwarning,showinfo,askyesno
from subprocess import Popen, PIPE
import urllib as parse
import urllib2 as request
import cPickle as pickle
import cookielib, socket
import sys,time,signal
import json,os,random,re,hashlib,stat

# -----------------------------START DNS cache for speed up-----------------------------
cachefile=os.path.expanduser('~/xfdown_cache')
origGetAddrInfo = socket.getaddrinfo
try:
    with open(cachefile, "rb") as f:
        dnscache=pickle.load(f)
except:
    dnscache={}

def getAddrInfoWrapper(host, port, family=0, socktype=0, proto=0, flags=0):
    if dnscache.has_key(host):
        return dnscache[host]
    else:
        dns=origGetAddrInfo(host, port, family, socktype, proto, flags)
        dnscache[host]=dns
        pickle.dump(dnscache, open(cachefile, "wb") , True)
        return dns
socket.getaddrinfo = getAddrInfoWrapper
# -----------------------------END DNS cache for speed up-----------------------------

def decode_u8(string):
    try:     return string.decode("u8")
    except:  return string

def hexchar2bin(hexchar):
    arry= bytearray()
    for i in range(0, len(hexchar), 2):
        arry.append(int(hexchar[i:i+2],16))
    return arry

def get_gtk(string):
    hashid = 5381
    for i in string:
        hashid += (hashid << 5) + ord(i)
    return hashid & 0x7fffffff;

class lwp_cookie(cookielib.LWPCookieJar):
    def save(self, filename=None, ignore_discard=False, ignore_expires=False,userinfo=None):
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError(MISSING_FILENAME_TEXT)

        if not os.path.exists(filename):
            f=open(filename,'w')
            f.close()
        f = open(filename, "r+")
        try:
            if userinfo:
                f.seek(0)
                f.write("#LWP-Cookies-2.0\n")
                f.write("#%s\n"%userinfo)
            else:
                f.seek(len(''.join(f.readlines()[:2])))
            f.truncate()
            f.write(self.as_lwp_str(ignore_discard, ignore_expires))
        finally:
            f.close()

global cookie_jar, cookie_path, download_path
cookie_path=os.path.expanduser('~/xfdown_cookie')
cookie_jar=lwp_cookie(cookie_path)
download_path=os.path.expanduser('~/Downloads')

class window_login(Toplevel):
    
    def md5(self,item):
        if sys.version_info >= (3,0):
            try:    item=item.encode("u8")
            except: pass
        return hashlib.md5(item).hexdigest().upper()
    
    def hash_word(self,password=None,verifycode=None,hashpasswd=None):
        if not hashpasswd:
            self.hashpasswd=self.md5(password)
        I=hexchar2bin(self.hashpasswd)
        if sys.version_info >= (3,0):
            H = self.md5(I + bytes(verifycode[2],encoding="ISO-8859-1"))
        else:
            H = self.md5(I + verifycode[2])
        G = self.md5(H + verifycode[1].upper())
        return G
    
    def load_config(self):
        os.chmod(self.config_path , stat.S_IREAD|stat.S_IWRITE)
        config_file=open(self.config_path)
        config=json.load(config_file)
        return config
    
    def save_config(self, SAVE=True):
        if not SAVE:
            config={"qq":'', "password":''}
        else:
            config={"qq":self.qqid, "password":self.qqpw}
        config_file=open(self.config_path,"w")
        json.dump(config,config_file)
        config_file.close()
        os.chmod(self.config_path , stat.S_IREAD|stat.S_IWRITE)
        return
    
    def __init__(self,parent):

        Toplevel.__init__(self,parent)
        self.title('QQ登录')
        self.parent=parent
        self.transient(parent)
        self.qqvc_validation=False
        self.config_path=os.path.expanduser('~/xfdown_config')
        self.remember_userinfo=False
        
        self.labelframe_login = LabelFrame(self)
        self.labelframe_login.grid(row=0, column=0, padx=5,pady=5)
        Label(self.labelframe_login, text="QQ:").grid(row=0,column=0,padx=5,pady=5)
        Label(self.labelframe_login, text="密码:").grid(row=1,column=0,padx=5,pady=5)
        Label(self.labelframe_login, text="验证码:").grid(row=2,column=0,padx=5,pady=5)
        self.entry_qqid = Entry(self.labelframe_login)
        self.entry_qqpw = Entry(self.labelframe_login, show='*')
        self.entry_qqvc = Entry(self.labelframe_login)
        self.entry_qqid.grid(row=0,column=1,padx=5,pady=5)
        self.entry_qqpw.grid(row=1,column=1,padx=5,pady=5)
        self.entry_qqvc.grid(row=2,column=1,padx=5,pady=5)        
        self.frame_image = Frame(self.labelframe_login)
        self.frame_image.grid(row=0, column=2,rowspan=2, padx=10, pady=10)
        self.image = Image.open("refresh.jpg")
        self.verifycode = ImageTk.PhotoImage(self.image)
        self.label_vc=Label(self.frame_image, image=self.verifycode)
        self.label_vc.grid(row=1, column=0)
        self.button_refresh=Button(self.labelframe_login,text='刷新',
                                   command=self.refresh_vc, width=8, padx=5,pady=5)
        self.button_refresh.grid(row=2,column=2)
        self.frame_login_cancel=Frame(self)
        self.frame_login_cancel.grid(row=1,column=0,sticky=W+E)
        self.checkbutton_save_config=Checkbutton(self.frame_login_cancel, text='记住用户名密码',
                                                 variable=self.remember_userinfo,
                                                 onvalue=True, offvalue=False)
        self.checkbutton_save_config.grid(row=0,column=0)
        self.button_login = Button(self.frame_login_cancel, text="登录",command=self.login)
        self.button_login.grid(row=0,column=1)
        self.button_cancel = Button(self.frame_login_cancel, text="取消",command=self.cancel)
        self.button_cancel.grid(row=0,column=2)
        for i in range(0,3):
            self.frame_login_cancel.columnconfigure(i, weight=1)
        
        self.bind("<Return>", self.login)
        self.bind("<Escape>", self.cancel)
        
        # check the config file
        if os.path.isfile(self.config_path):
            config_data=self.load_config()
            if not config_data['qq']=='':
                self.entry_qqid.delete(0,END)
                self.entry_qqid.insert(END,config_data['qq'])
                self.entry_qqpw.delete(0,END)
                self.entry_qqpw.insert(END,config_data['password'])
                self.refresh_vc()
                self.initial_focus = self.entry_qqvc
                self.initial_focus.focus_set()
            else:
                self.initial_focus = self.entry_qqid
                self.initial_focus.focus_set()
        else:
            self.initial_focus = self.entry_qqid
            self.initial_focus.focus_set()

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,parent.winfo_rooty()+50))
        self.wait_window(self)


   
    def request_url(self,url,data=None,savecookie=False):
        if data:
            data = parse.urlencode(data).encode('utf-8')
            fp=request.urlopen(url,data)
        else:
            fp=request.urlopen(url)
        try:
            string = fp.read().decode('utf-8')
        except UnicodeDecodeError:
            string = fp.read()
        if savecookie == True:
            cookie_jar.save(ignore_discard=True, ignore_expires=True,userinfo="%s#%s"%(self.qqid,self.qqhash))
        fp.close()
        return string
    
    def refresh_vc(self):
        self.qqid=self.entry_qqid.get().strip()
        try:
            if eval(self.qqid)>10000:
                # validate the QQ id，QQ ID starts from 10001
                urlv = 'http://check.ptlogin2.qq.com/check?uin=%s&appid=567008010&r=%s'%(self.qqid,random.Random().random())
                string = self.request_url(url=urlv)
                self.qqvc=eval(string.split("(")[1].split(")")[0])
                self.qqvc=list(self.qqvc)
                if self.qqvc[0]=='1':
                    imgurl="http://captcha.qq.com/getimage?aid=567008010&r=%s&uin=%s"%(random.Random().random(),self.qqid)
                    f=open('verify.jpg',"wb")
                    fp = request.urlopen(imgurl)
                    f.write(fp.read())
                    f.close()
                    self.image = Image.open("verify.jpg")
                    self.verifycode = ImageTk.PhotoImage(self.image)
                    self.label_vf=Label(self.frame_image, image=self.verifycode)
                    self.label_vf.grid(row=1, column=0)
                elif self.qqvc[0]=='0':
                    self.image = Image.open("blank.jpg")
                    self.verifycode = ImageTk.PhotoImage(self.image)
                    self.label_vf=Label(self.frame_image, image=self.verifycode)
                    self.label_vf.grid(row=1, column=0)   
                self.qqvc_validation=True
            else:
                showerror('','请输入有效QQ号码')
                return                 
        except:
            showerror('','请输入有效QQ号码')
        return
     
    def login_info(self):
        self.request_url(url ="http://lixian.qq.com/handler/log_handler.php",data={'cmd':'stat'},savecookie=True)
        urlv = 'http://lixian.qq.com/handler/lixian/do_lixian_login.php'
        f = open(cookie_path)
        fi = re.compile('skey="([^"]+)"')
        skey = fi.findall("".join(f.readlines()))[0]
        f.close()
        string = self.request_url(url =urlv,data={"g_tk":get_gtk(skey)},savecookie=True)
        return string
        
    def login(self,ENTER=True):
        try:
            if eval(self.entry_qqid.get().strip())<=10000:
                showerror('','请输入有效QQ号码')
                return
        except:
            showerror('','请输入有效QQ号码')
            return
        
        if self.qqvc_validation==False or self.entry_qqvc.get().strip()=='':
            showerror('','请输入验证码')
            self.refresh_vc()
        else:
            self.qqid=self.entry_qqid.get().strip()
            self.qqpw=self.entry_qqpw.get().strip()
            if self.qqvc[0]=='1':
                self.qqvc[1]=self.entry_qqvc.get().strip()
            self.qqhash=self.hash_word(self.qqpw, self.qqvc)
            urlv="http://ptlogin2.qq.com/login?u=%s&p=%s&verifycode=%s"%(self.qqid,self.qqhash,self.qqvc[1])+"&aid=567008010&u1=http%3A%2F%2Flixian.qq.com%2Fmain.html&h=1&ptredirect=1&ptlang=2052&from_ui=1&dumy=&fp=loginerroralert&action=2-10-&mibao_css=&t=1&g=1"
            login_result = self.request_url(url = urlv)       
            if login_result.find(decode_u8('登录成功')) != -1:
                foo = self.login_info() # foo is a unused variable
                self.save_config(self.remember_userinfo)
                self.parent.userinfo=self.qqid
                self.parent.title('QQ离线:%s'%self.qqid)
                self.parent.get_list()
                self.parent.refresh_listbox()
                self.parent.load_history()
                self.parent.refresh_list_local()
                self.cancel()
            elif login_result.find(decode_u8('验证码不正确')) != -1:
                showerror('','验证码不正确')
                self.refresh_vc()
            elif login_result.find(decode_u8('不正确')) != -1:
                showerror('','帐号或者密码不正确')
                self.refresh_vc()
            else:
                showerror('','登录失败')
                self.refresh_vc()
        
    def cancel(self,ESCAPE=True):
        self.destroy()





class window_main(Tk):
    
    def swap(self,x,y):
        self.filename[y],self.filename[x]=self.filename[x],self.filename[y]
        self.filehash[y],self.filehash[x]=self.filehash[x],self.filehash[y]
        self.filemid[y],self.filemid[x]=self.filemid[x],self.filemid[y]
        self.filesize[y], self.filesize[x]=self.filesize[x], self.filesize[y]
        self.file_size[y],self.file_size[x]=self.file_size[x],self.file_size[y]
        self.file_name[y],self.file_name[x]=self.file_name[x],self.file_name[y]
        self.file_progress[y],self.file_progress[x]=self.file_progress[x],self.file_progress[y]
   
    def pop_menu(self, event):
        x=self.listbox_qqdrive.nearest(event.y)
        if str(x) in self.listbox_qqdrive.curselection():
            self.menu_context.post(event.x_root, event.y_root)
        else:
            self.listbox_qqdrive.select_clear(0, END)
            self.listbox_qqdrive.select_set(x)
            self.menu_context.post(event.x_root, event.y_root)         
    
    def pop_menu_local(self, event):
        x=self.listbox_local.nearest(event.y)
        if str(x) in self.listbox_local.curselection():
            self.menu_context_local.post(event.x_root, event.y_root)
        else:
            self.listbox_local.select_clear(0, END)
            self.listbox_local.select_set(x)
            self.menu_context_local.post(event.x_root, event.y_root)
    
    def fold_menu(self,event):
        self.menu_context.unpost()
        self.menu_context_local.unpost()
    
    def __init__(self,login_status):
        Tk.__init__(self)        
        self.title('QQ旋风离线下载')
        self.resizable(0, 0)
        self.sorting_order=-1
        self.userinfo=''
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        # Command buttons     
        frame_remote_button = Frame(self, padx=5, pady=5,relief=GROOVE)
        frame_remote_button.configure(borderwidth=2)
        frame_remote_button.grid(row =0,column=0,columnspan=1,padx=10, pady=10,sticky=W+E)
        for i in range(0,5):
            frame_remote_button.columnconfigure(i, weight=1)
        button_download = Button(frame_remote_button,text = '下载',command=self.download)
        button_refresh = Button(frame_remote_button,text = '刷新',command=self.refresh_list)
        button_add = Button(frame_remote_button,text = '添加',command=self.add_task)
        button_delete = Button(frame_remote_button, text = '删除', command=self.del_task)
        button_sort = Menubutton(frame_remote_button, text = '排序',relief=RAISED) 
        button_download.grid(row=0, column=0, padx=5, pady=5)
        button_refresh.grid(row=0, column=1, padx=5, pady=5)
        button_add.grid(row=0, column=2, padx=5, pady=5)
        button_delete.grid(row=0, column=3, padx=5, pady=5)
        button_sort.grid(row=0, column=4, padx=5, pady=5)
        frame_local_button = Frame(self, padx=5, pady=5,relief=GROOVE)
        frame_local_button.configure(borderwidth=2)
        for i in range(0,5):
            frame_local_button.columnconfigure(i, weight=1)
        frame_local_button.grid(row =0,column=1,columnspan=1,padx=10, pady=10,sticky=W+E)
        button_resume = Button(frame_local_button, text = '启动', command=self.resume)
        button_pause = Button(frame_local_button, text = '暂停', command=self.pause)
        button_remove = Button(frame_local_button, text = '删除', command=self.remove)
        button_aria = Button(frame_local_button, text = 'aria', command=self.refresh_list_local)
        button_quit = Button(frame_local_button, text = '退出', command=self.exit)
        button_resume.grid(row=0,column=0, padx=5, pady=5)
        button_pause.grid(row=0,column=1, padx=5, pady=5)
        button_remove.grid(row=0,column=2, padx=5, pady=5)
        button_aria.grid(row=0,column=3, padx=5, pady=5)
        button_quit.grid(row=0,column=4, padx=5, pady=5)
        
        # Menu-Sort_list
        button_sort.menu=Menu(button_sort,tearoff=0)
        button_sort['menu']=button_sort.menu
        button_sort.menu.add_command ( label="大小", command=lambda:self.sort_list('size'))
        button_sort.menu.add_command ( label="进度", command=lambda:self.sort_list('progress'))
        button_sort.menu.add_command ( label="名称", command=lambda:self.sort_list('name'))
        # Remote list box
        frame_remote_list = LabelFrame(self,text='离线资源', padx=5, pady=5, labelanchor=NE)
        frame_remote_list.grid(row =1,column=0,padx=10, pady=10,sticky=W+E)
        self.listbox_qqdrive = Listbox(frame_remote_list, selectmode=EXTENDED, width=40,height=10)
        self.listbox_qqdrive.grid(column=0, row=0,sticky=W+E)  
        scroll_y = Scrollbar(frame_remote_list, orient=VERTICAL, command=self.listbox_qqdrive.yview)
        scroll_y.grid(column=1, row=0, sticky=N+S)
        self.listbox_qqdrive['yscrollcommand'] = scroll_y.set
        scroll_x = Scrollbar(frame_remote_list, orient=HORIZONTAL, command=self.listbox_qqdrive.xview)
        scroll_x.grid(row=1, sticky=W+E)
        self.listbox_qqdrive['xscrollcommand'] = scroll_x.set
        # Pop-up menus for remote list
        self.bind("<Button-1>", self.fold_menu)
        self.listbox_qqdrive.bind("<Button-3>", self.pop_menu)
        self.menu_context = Menu(self, tearoff=0)
        self.menu_context.add_command(label="下载", command=self.download)
        self.menu_context.add_command(label="删除", command=self.del_task) 
        # Local list box
        frame_local_list = LabelFrame(self,text='本地任务', padx=5, pady=5, labelanchor=NE)
        frame_local_list.grid(row =1,column=1,padx=10, pady=10,sticky=W+E)
        self.listbox_local = Listbox(frame_local_list, selectmode=EXTENDED, width=40,height=10)
        self.listbox_local.grid(column=0, row=0,sticky=W+E)  
        scroll_y_local = Scrollbar(frame_local_list, orient=VERTICAL, command=self.listbox_local.yview)
        scroll_y_local.grid(column=1, row=0, sticky=N+S)
        self.listbox_local['yscrollcommand'] = scroll_y_local.set
        scroll_x_local = Scrollbar(frame_local_list, orient=HORIZONTAL, command=self.listbox_local.xview)
        scroll_x_local.grid(column=0,row=1, sticky=W+E)
        self.listbox_local['xscrollcommand'] = scroll_x_local.set
        # Pop-up menus for local list
        self.listbox_local.bind("<Button-3>", self.pop_menu_local)
        self.menu_context_local = Menu(self, tearoff=0)
        self.menu_context_local.add_command(label="启动", command=self.resume)
        self.menu_context_local.add_command(label="暂停", command=self.pause)
        self.menu_context_local.add_command(label="删除", command=self.remove) 
  
        # Center the main window
        self.update_idletasks()
        size_x = self.winfo_width()
        size_y = self.winfo_height()
        pos_x = (self.winfo_screenwidth() // 2) - (size_x // 2)
        pos_y = (self.winfo_screenheight() // 2) - (size_y // 2)
        self.geometry('+{}+{}'.format(pos_x, pos_y))
        
        # Check login_status
        if login_status:
            f=open(cookie_path,'r')
            f.readline()
            s=f.readline()
            f.close()
            self.userinfo=s.split('#')[1]
            self.title('QQ离线:%s'%self.userinfo)
            self.get_list()
            self.refresh_listbox()
            self.load_history()
            self.refresh_list_local()
        else:
            window_login(self) 
    
    def load_history(self):
        self.local_history=os.path.expanduser('~/%s_history'%self.userinfo)
        self.file_status_local=[]
        self.file_size_local=[]
        self.file_name_local=[]
        self.cmds_local=[]
        self.aria=[]
        if not os.path.isfile(self.local_history):
            return
        else:
            os.chmod(self.local_history , stat.S_IREAD|stat.S_IWRITE)
            history_file=open(self.local_history)
            history=json.load(history_file)
            history_file.close()
            for item in history:
                self.file_status_local.append(item[0])
                self.file_size_local.append(item[1])
                self.file_name_local.append(item[2])
                self.cmds_local.append(item[3])
                self.aria.append('')
                
              
    def save_history(self):
        history=zip(self.file_status_local,self.file_size_local,self.file_name_local,self.cmds_local)
        history_file=open(self.local_history,"w")
        json.dump(history,history_file)
        history_file.close()
        os.chmod(self.local_history, stat.S_IREAD|stat.S_IWRITE)
        
    def get_url(self,url,data=None):
        # Communicate with the QQ-lixian server 
        if data:
            data = parse.urlencode(data).encode('utf-8')
            fp=request.urlopen(url,data)
        else:
            fp=request.urlopen(url)
        try:
            string = fp.read().decode('utf-8')
        except UnicodeDecodeError:
            string = fp.read()
        fp.close()
        return string
  
    def get_list(self):
        # Get the remote list
        urlv = 'http://lixian.qq.com/handler/lixian/get_lixian_items.php'
        res = self.get_url(urlv, {'page': 0, 'limit': 200})
        res = json.JSONDecoder().decode(res)
        if not res["data"]:
            showinfo('','无离线任务')
        else:
            self.filename = []
            self.filehash = []
            self.filemid = []
            self.filesize=[]
            self.file_name=[] # Human readable file name
            self.file_size=[]  # Human readable size
            self.file_progress=[]
            self.filestatus=[]

            for num in range(len(res['data'])):
                index=res['data'][num]
                self.filename.append(index['file_name'].split('\\')[-1].encode("u8"))
                self.filehash.append(index['hash'])
                size=index['file_size']
                self.filemid.append(index['mid'])
                if size==0:
                    progress="-0"
                else:
                    progress=str(index['comp_size']/size*100).split(".")[0]
 
                self.filesize.append(size)
                self.file_progress.append(progress)
                self.file_name.append(decode_u8(self.filename[num]))

                if eval(progress)==100:
                    self.filestatus.append(True)
                else:
                    self.filestatus.append(False)
                
                unit=["B","K","M","G"]                
                for i in range(4):
                    _unit=unit[i]
                    if size>=1024:
                        size=size/1024
                    else:
                        break
                size="%.1f%s"%(size,_unit)
                self.file_size.append(size)
                
        
    def get_source_address(self,filelist):
        # Get the download address for remote files
        urlv = 'http://lixian.qq.com/handler/lixian/get_http_url.php'
        self.filehttp = [''] * len(self.filehash)
        self.filecom = [''] * len(self.filehash)
        for num in filelist:
            data = {'hash':self.filehash[num],'filename':self.filename[num],'browser':'other'}
            string = self.get_url(urlv,data)
            self.filehttp[num]=(re.search(r'\"com_url\":\"(.+?)\"\,\"',string).group(1))
            self.filecom[num]=(re.search(r'\"com_cookie":\"(.+?)\"\,\"',string).group(1))
        return
    
    def refresh_list(self):
        # Update the remote file list
        if not check_login(cookie_path):
            window_login(self)
        else:
            self.get_list()
            self.refresh_listbox()
    
    def refresh_listbox(self):
        # Update the remote file listbox
        if not hasattr(self,'filesize') or len(self.filesize)==0:
            return
        self.listbox_qqdrive.delete(0, END)
        for i in range (0,len(self.filesize)):
            if self.file_progress[i]=='100':  item_color='blue'
            else:  item_color='purple'
            self.listbox_qqdrive.insert(END,'['+str(i+1)+']|'+self.file_progress[i]+'%|'+self.file_size[i]+'|'+self.file_name[i])
            self.listbox_qqdrive.itemconfig(self.listbox_qqdrive.size()-1,fg=item_color)

    def download(self):
        task_index=map(int,self.listbox_qqdrive.curselection())
        if task_index==[]:
            showwarning('','尚未选择文件')
        else:
            if askyesno('下载','确认下载%d项任务？'%(len(task_index))):
                try:
                    self.get_source_address(task_index)
                    for i in task_index:
                        if self.filestatus[i]==False:
                            showwarning('','请选择已完成的离线资源')
                            self.listbox_qqdrive.select_clear(0,END)
                            return 
                    local_index=[] # Keep the selections so it wont's be lost when refresh listbox
                    for i in task_index:
                        cmd=['aria2c', '-c', '-s10', '-x10', '--header',
                             'Cookie: FTN5K=%s'%self.filecom[i], '%s'%self.filehttp[i]
                             ,'--summary-interval=2']                                         
                        if not self.file_name[i] in self.file_name_local:
                            self.file_status_local.append('terminated')
                            self.file_name_local.append(self.file_name[i])
                            self.file_size_local.append(self.file_size[i])
                            self.cmds_local.append(cmd)
                            self.aria.append('')
                            self.refresh_list_local()
                            local_index.append(self.file_name_local.index(self.file_name[i]))
                        elif self.file_name[i] in self.file_name_local:
                            k=self.file_name_local.index(self.file_name[i])
                            self.cmds_local[k]=cmd
                            if not k in local_index:
                                local_index.append(k)
                    for i in local_index:
                        self.listbox_local.select_set(i)                   
                    self.resume()   
                except:
                    showerror('','无法下载，请刷新列表或重试')                                 
        return
    
    def add_task(self):
        print 'Add Task'
        
    def del_task(self):
        task_index=map(int,self.listbox_qqdrive.curselection())
        if task_index==[]:
            showwarning('','尚未选择文件')
        else:
            if askyesno('删除','确认删除%d项任务？'%(len(task_index))):
                try:
                    for i in task_index:
                        if self.filestatus[i]=='downloading':
                            showwarning('','有文件正在下载中')
                            return               
                    urlv = 'http://lixian.qq.com/handler/lixian/del_lixian_task.php'
                    for i in task_index:
                        data={'mids':self.filemid[i]}
                        self.get_url(urlv,data)
                        self.refresh_list()
                except:
                    showerror('','无法删除，请刷新列表或重试')
        return
    
    def sort_list(self,option):
        #Only sort the stored list
        if not hasattr(self,'filesize'):
            # No remote files
            return
        elif len(self.filesize)==1:
            return
        elif option=='progress':
            if  self.sorting_order==1:
                for i in range(0,len(self.file_progress)):
                    for j in range(0,len(self.file_progress)):
                            if eval(self.file_progress[j]) > eval(self.file_progress[i]):
                                self.swap(i,j)
            else:
                for i in range(0,len(self.file_progress)):
                    for j in range(0,len(self.file_progress)):
                            if eval(self.file_progress[j]) < eval(self.file_progress[i]):
                                self.swap(i,j)    
        elif option=='size':
            if  self.sorting_order==1:
                for i in range(0,len(self.filesize)):
                    for j in range(0,len(self.filesize)):
                        if self.filesize[j] > self.filesize[i]:
                            self.swap(i,j)
            else:
                for i in range(0,len(self.filesize)):
                    for j in range(0,len(self.filesize)):
                        if self.filesize[j] < self.filesize[i]:
                            self.swap(i,j)
                        
        elif option=='name':
            if  self.sorting_order==1:
                for i in range(0,len(self.filename)):
                    for j in range(0,len(self.filename)):
                        if self.filename[j] > self.filename[i]:
                            self.swap(i, j)
            else:
                for i in range(0,len(self.filename)):
                    for j in range(0,len(self.filename)):
                        if self.filename[j] < self.filename[i]:
                            self.swap(i, j)
        self.sorting_order=self.sorting_order*(-1)
        self.refresh_listbox()
        
    def resume(self):
        # Resume local unfinished task
        task_index=map(int,self.listbox_local.curselection())
        if task_index==[]:
            return
        else:
            try:
                for i in task_index:
                    if self.file_status_local[i] in ['downloading','done']:
                        continue
                    elif self.file_status_local[i] in ['terminated','missing']:
                        print 'resumed'
                        self.file_status_local[i]='downloading'
                        self.aria[i]=Popen(self.cmds_local[i],cwd=download_path)
                    elif self.file_status_local[i]=='paused':
                        print 'paused'
                        self.aria[i].send_signal(signal.SIGCONT)
            except:
                showerror('','无法下载，请刷新列表或重试')
        self.refresh_list_local()
              
    def pause(self):
        # Pause download task
        task_index=map(int,self.listbox_local.curselection())
        if task_index==[]:
            return
        else:
            for i in task_index:
                if self.file_status_local[i]=='downloading':
                    try:
                        self.aria[i].send_signal(signal.SIGSTOP)
                        self.file_status_local[i]='paused'
                    except:
                        continue
        self.refresh_list_local()
        
    def remove(self):
        pass
    
    def refresh_list_local(self):
        # Check running status
        for i in range(0,len(self.aria)):
            if hasattr(self.aria[i],'poll'):
                if self.aria[i].poll()==0:
                    self.file_status_local[i]='done'
                    self.aria[i].terminate()
                    self.aria[i]=''
        for i in range(0,len(self.file_name_local)):
            f=os.path.expanduser('~/Downloads/%s'%self.file_name_local[i])
            if not os.path.isfile(f) and self.file_status_local[i]=='done':
                self.file_status_local[i]='missing'
        self.refresh_listbox_local()
    
    def refresh_listbox_local(self):
        # Update the local file listbox
        if not hasattr(self,'file_status_local') or len(self.file_status_local)==0:
            return
        self.listbox_local.delete(0, END)
        for i in range (0,len(self.file_status_local)):
            if self.file_status_local[i]=='done':
                item_color='blue'
            elif self.file_status_local[i]=='downloading':
                item_color='cyan'
            elif self.file_status_local[i]=='missing':
                item_color='red'
            elif self.file_status_local[i] in ['terminated','paused']:
                item_color='black'
            self.listbox_local.insert(END,'['+str(i+1)+']|'+self.file_status_local[i]+'|'+
                                      self.file_size_local[i]+'|'+self.file_name_local[i])
            self.listbox_local.itemconfig(END,fg=item_color)
    
    def exit(self): 
        for i in range (0,len(self.aria)):
            if hasattr(self.aria[i],'terminate'):
                self.aria[i].terminate()
                self.aria[i]=''
                self.file_status_local[i]='terminated'
        self.save_history()
        self.quit()

def check_login(cookiepath):    
    status=False
    if os.path.isfile(cookiepath):
        try:
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            status=True
        except:
            pass
    opener = request.build_opener(request.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0'),("Referer","http://lixian.qq.com/main.html")]
    request.install_opener(opener)
    return status

if __name__== '__main__':
    window_main(check_login(cookie_path)).mainloop()
