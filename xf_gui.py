#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from Tkinter import *
from PIL import Image, ImageTk
from tkMessageBox import showerror,showwarning,showinfo,askyesno
from subprocess import Popen
import urllib as parse
import urllib2 as request
import cPickle as pickle
import cookielib, socket
import sys,time
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

global cookie_jar, cookie_path
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
        self.frame_login_cancel.columnconfigure(0, weight=1)
        self.frame_login_cancel.columnconfigure(1, weight=1)
        self.frame_login_cancel.columnconfigure(2, weight=1)
        
        self.bind("<Return>", self.login)
        self.bind("<Escape>", self.cancel)
        
        # 检查是否存在config文件并从中读取用户密码信息
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
                # 检查QQ号码是否有效，最小的QQ号码是10001
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
                self.parent.get_list()
                self.parent.refresh_listbox()
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
 
    def __init__(self,login_status):
        Tk.__init__(self)        
        self.title('QQ旋风离线下载')
        self.resizable(0, 0)
        self.sorting_order=-1
        # 创建命令按钮     
        frame_button = Frame(self, padx=5, pady=5,relief=GROOVE)
        frame_button.configure(borderwidth=2)
        frame_button.grid(row =0,padx=10, pady=10,sticky=W+E)
        frame_button.columnconfigure(0, weight=1)
        frame_button.columnconfigure(1, weight=1)
        frame_button.columnconfigure(2, weight=1)
        frame_button.columnconfigure(3, weight=1)
        frame_button.columnconfigure(4, weight=1)
        frame_button.columnconfigure(5, weight=1)
        button_download = Button(frame_button,text = '下载',command=self.download)
        button_refresh = Button(frame_button,text = '刷新',command=self.refresh_list)
        button_add = Button(frame_button,text = '添加',command=self.add_task)
        button_delete = Button(frame_button, text = '删除', command=self.del_task)
        button_sort = Menubutton(frame_button, text = '排序',relief=RAISED) 
        button_quit = Button(frame_button, text = '退出', command=self.quit)   
        button_download.grid(row=0, column=0, padx=5, pady=5)
        button_refresh.grid(row=0, column=1, padx=5, pady=5)
        button_add.grid(row=0, column=2, padx=5, pady=5)
        button_delete.grid(row=0, column=3, padx=5, pady=5)
        button_sort.grid(row=0, column=4, padx=5, pady=5)
        button_quit.grid(row=0, column=5, padx=5, pady=5)
        # 按钮菜单-排序
        button_sort.menu=Menu(button_sort,tearoff=0)
        button_sort['menu']=button_sort.menu
        button_sort.menu.add_command ( label="大小", command=lambda:self.sort_list('size'))
        button_sort.menu.add_command ( label="进度", command=lambda:self.sort_list('progress'))
        button_sort.menu.add_command ( label="名称", command=lambda:self.sort_list('name'))
        # 创建列表框
        frame_list = LabelFrame(self,text='资源列表', padx=5, pady=5, labelanchor=NE)
        frame_list.grid(row =1,padx=10, pady=10,sticky=W+E)
        self.listbox_qqdrive = Listbox(frame_list, selectmode=MULTIPLE, width=50,height=10)
        self.listbox_qqdrive.grid(column=0, row=0,sticky=W+E)  
        scroll_y = Scrollbar(frame_list, orient=VERTICAL, command=self.listbox_qqdrive.yview)
        scroll_y.grid(column=1, row=0, sticky=N+S)
        self.listbox_qqdrive['yscrollcommand'] = scroll_y.set
        scroll_x = Scrollbar(frame_list, orient=HORIZONTAL, command=self.listbox_qqdrive.xview)
        scroll_x.grid(row=1, sticky=W+E)
        self.listbox_qqdrive['xscrollcommand'] = scroll_x.set       
        # Center the main window
        self.update_idletasks()
        size_x = self.winfo_width()
        size_y = self.winfo_height()
        pos_x = (self.winfo_screenwidth() // 2) - (size_x // 2)
        pos_y = (self.winfo_screenheight() // 2) - (size_y // 2)
        self.geometry('+{}+{}'.format(pos_x, pos_y))
        #检查是否需要QQ登录
        if login_status:
            self.get_list()
            self.refresh_listbox()
        else:
            window_login(self) 
   
    def get_url(self,url,data=None):
        ##向QQ旋风服务器请求数据 
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
        #获取离线资源列表
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

            for num in range(len(res['data'])):
                index=res['data'][num]
                self.filename.append(index['file_name'].encode("u8"))
                self.filehash.append(index['hash'])
                size=index['file_size']
                self.filemid.append(index['mid'])
                if size==0:
                    progress="-0"
                else:
                    progress=str(index['comp_size']/size*100).split(".")[0]
 
                self.filesize.append(size)
                
                unit=["B","K","M","G"]                
                for i in range(4):
                    _unit=unit[i]
                    if size>=1024:
                        size=size/1024
                    else:
                        break
                size="%.1f%s"%(size,_unit)
                self.file_progress.append(progress)
                self.file_size.append(size)
                self.file_name.append(decode_u8(self.filename[num]))
        
    def get_source_address(self,filelist):
        #获取资源原始下载地址
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
        #更新离线资源列表
        if not check_login(cookie_path):
            window_login(self)
        else:
            self.get_list()
            self.refresh_listbox()
    
    def refresh_listbox(self):
        #更新GUI列表框
        if not hasattr(self,'filesize') or len(self.filesize)==0:
            return
        self.listbox_qqdrive.delete(0, END)
        for i in range (0,len(self.filesize)):
            if self.file_progress[i]=='100':  item_color='blue'
            else:  item_color='purple'
            self.listbox_qqdrive.insert(END,'#'+str(i+1)+'#|'+self.file_progress[i]+'% | '+self.file_size[i]+' | '+self.file_name[i])
            self.listbox_qqdrive.itemconfig(self.listbox_qqdrive.size()-1,fg=item_color)

    def download(self):
        task_index=map(int,self.listbox_qqdrive.curselection())
        if task_index==[]:
            showwarning('','尚未选择要下载文件')
        else:
            if askyesno('下载任务','确认下载%d项任务？'%(len(task_index))):
                try:
                    self.get_source_address(task_index)
                    cmds=[]
                    task=[]
                    for i in task_index:
                        if eval(self.file_progress[i])<100:
                            showwarning('','请选择完成度100%的资源下载')
                            self.listbox_qqdrive.select_clear(0,END)
                            return
                        cmd=['aria2c', '-c', '-s10', '-x10', '--header', 'Cookie: FTN5K=%s'%self.filecom[i], '%s'%self.filehttp[i]]
                        cmds.append(cmd)
                        task.append((i,self.file_name[i]))
                    for j in range(len(cmds)):
                        aria=Popen(cmds[j],cwd=download_path)
                        aria.wait()
                        try:                    
                            Popen(["notify-send",task[j][1],"旋风离线下载完成"])
                            self.listbox_qqdrive.select_clear(task[j][0])
                        except:
                            print ('Download completed.')
#                         if os.name=='posix': print("notify-send error,you should have libnotify-bin installed.")
                except:
                    showerror('','无法下载，请刷新列表或重试')                                 
        return
    
    def add_task(self):
        print 'Add Task'
        
    def del_task(self):
        task_index=map(int,self.listbox_qqdrive.curselection())
        if task_index==[]:
            showwarning('','尚未选择要删除文件')
        else:
            if askyesno('删除任务','确认删除%d项任务？'%(len(task_index))):
                try:                    
                    urlv = 'http://lixian.qq.com/handler/lixian/del_lixian_task.php'
                    for i in task_index:
                        data={'mids':self.filemid[i]}
                        self.get_url(urlv,data)
                        self.refresh_list()
                except:
                    showerror('','无法删除，请刷新列表或重试')
        return
    
    def sort_list(self,option):
        #列表排序，只排序列表，不刷新列表
        if not hasattr(self,'filesize'):
            showinfo('','无任务列表')
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
                        if eval(self.filesize[j]) > eval(self.filesize[i]):
                            self.swap(i,j)
            else:
                for i in range(0,len(self.filesize)):
                    for j in range(0,len(self.filesize)):
                        if eval(self.filesize[j]) < eval(self.filesize[i]):
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

window_main(check_login(cookie_path)).mainloop()
