>>> import os  
 
>>> import statvfs  
 
>>> vfs=os.statvfs("/home")  
 
>>> vfs  
 
(4096, 4096, 70959944, 70058799, 66396080, 73269248, 73234981, 73234981, 0, 255)  

>>> available=vfs[statvfs.F_BAVAIL]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)  
 
>>> available  (可用空间)
 
253 
 
>>> capacity=vfs[statvfs.F_BLOCKS]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)  
 
>>> capacity  （空间总量）
 
270 
 
>>> used=capacity-available  
 
>>> used  （已用空间）
17 
