# XF_GUI，QQ旋风GUI

基于kikyous的XF_TUI for Linux，通过Tkinter进行了实现。

kikyous的XF_TUI for Linux地址：https://github.com/kikyous/xfdown

![](https://github.com/spartty/xf_gui/blob/alpha/screenshot.png)


现有功能：
登录，远程资源列表，下载/删除，列表排序，右键菜单，本地任务列表，本地任务控制(开始/暂停/继续)，实时console输出

To do list：
添加远程任务，删除本地任务

问题：
如何确定远程文件与本地任务的一一对应关系？比如两个文件文件名大小完全相同，但一个来自ed2k,一个来自bt。
远程任务A，下载到本地50%的时候暂停，删除远程文件A，重新添加远程文件A，本地启动任务A，任务无法启动。
