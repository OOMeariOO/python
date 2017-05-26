#coding: utf-8

# @Author: 米 雷
# @File: SigleList.py
# @Time: 2017/5/26
# @Contact: 1262585769@qq.com
# @Description: 设计一个链表
#               获取一个模块或者类中的所有方法及参数列表

class Node(object):
    def __init__(self, data, next = None):
        self.data = data
        self._next = next

class SingleLinkedList(object):

    def __init__(self):
        self.root = None
        #self.size = 0

    #在链表尾部添加新节点
    def append(self, value):
        item = None
        if isinstance(value, Node):
            item = value
        else:
            item = Node(value)
        if not self.root:
            self.root = item
        else:
            node = self.root
            while node._next:
                node = node._next
            node._next = item

    #在链表首部添加节点
    def prepend(self, value):
        if self.root == None:
            self.root = Node(value, None)
        else:
            newroot = Node(value, None)
            #更新root索引
            newroot._next = self.root
            self.root = newroot

    #在链表的指定位置添加节点
    def insert(self, index, value):
        if self.root == None:
            return
        if index <= 0 or index > self.mysize():
            print 'index %d 非法， 应该审视一下您的插入节点在整个链表的位置！' % index
            return
        elif index == 1:
            #如果index==1，则在链表首部添加即可
            self.prepend(value)
        elif index == self.mysize() + 1:
            #如果index正好比当前链表长度大1，则添加在链表的尾部即可
            self.append(value)
        else:
            #如果在链表中部添加新的节点，直接进行添加即可。
            counter = 2
            pre = self.root
            cursor = self.root._next
            while cursor != None:
                if counter == index:
                    temp = Node(value, None)
                    pre._next = temp
                    temp._next = cursor
                    break
                else:
                    counter += 1
                    pre = cursor
                    cursor = cursor._next

    #删除指定位置上的节点
    def delNode(self, index):
        if self.root == None:
            return
        if index <= 0 or index > self.mysize():
            return
        #对第一个位置需要小心处理
        if index == 1:
            self.root = self.root._next
        else:
            pre = self.root
            cursor = pre._next
            counter = 2
            while cursor != None:
                if index == counter:
                    print 'can be here!'
                    pre._next = cursor._next
                    break
                else:
                    pre = cursor
                    cursor = cursor._next
                    counter += 1

    #删除值为value的链表节点元素
    def delValue(self, value):
        if self.root == None:
            return
        #对第一个位置需要小心处理
        if self.root.data == value:
            self.root = self.root._next
        else:
            pre = self.root
            cursor = pre._next
            while cursor != None:
                if cursor.data == value:
                    pre._next = cursor._next
                    #千万记得要更新这个节点，否则会出现死循环。。。
                    cursor = cursor._next
                    continue
                else:
                    pre = cursor
                    cursor = cursor._next

    #判断链表是否为空
    def isempty(self):
        if self.root == None or self.mysize() == 0:
            return True
        else:
            return False

    #删除链表及其内部所有元素
    def truncate(self):
        if self.root == None or self.mysize() == 0:
            return
        else:
            cursor = self.root
            while cursor != None:
                cursor.data = None
                cursor = cursor._next
            self.root = None
            cursor = None

    #获取指定位置的节点的值
    def getvalue(self, index):
        if self.root is None or self.mysize() == 0:
            print '当前链表为空！'
            return None
        if index <= 0 or index > self.mysize():
            print 'index %d 不合法' % index
            return None
        else:
            counter = 1
            cursor = self.root
            while cursor is not None:
                if index == counter:
                    return cursor.data
                else:
                    counter += 1
                    cursor = cursor._next

    #获取链表尾部的值， 且不删除该尾部节点
    def peek(self):
        return self.getvalue(self.mysize())

    #获取链表尾部节点的值，并删除该尾部节点
    def pop(self):
        if self.root is None or self.mysize() == 0:
            print '当前链表为空！'
            return None
        elif self.mysize() == 1:
            top = self.root.data
            self.root = None
            return top
        else:
            pre = self.root
            cursor = pre._next
            while cursor._next is not None:
                pre = cursor
                cursor = cursor._next
            top = cursor.data
            cursor = None
            pre._next = None
            return top

    #单链表逆序实现
    def reverse(self):
        if self.root is None:
            return
        if self.mysize() == 1:
            return
        else:
            # post = None
            pre = None
            cursor = self.root
            while cursor is not None:
                #'逆序操作'
                post = cursor._next
                cursor._next = pre
                pre = cursor
                cursor = post
            #千万不要忘记了把逆序后的头节点赋值给root,否则无法正确显示
            self.root = pre

    #删除链表中的重复元素
    def defDuplecate(self):
        #使用一个map来存放即可，类似于变性的“桶排序”
        dic = {}
        if self.root == None:
            return
        if self.mysize() == 1:
            return
        pre = self.root
        cursor = pre._next
        #为字典赋值
        temp = self.root._next
        while temp != None:
            dic[str(temp.data)] = 0
            temp = temp._next
        temp = None
        dic[str(self.root.data)] = 1
        #开始实施删除重复元素的操作
        while cursor != None:
            if dic[str(cursor.data)] == 1:
                pre._next = cursor._next
                cursor = cursor._next
            else:
                dic[str(cursor.data)] += 1
                pre = cursor
                cursor = cursor._next

    #修改指定位置节点的值
    def updateNode(self, index, value):
        if self.root == None:
            return
        if index <= 0 or index > self.mysize():
            return
        if index == 1:
            self.root.data = value
            return
        else:
            cursor = self.root._next
            counter = 2
            while cursor != None:
                if counter == index:
                    cursor.data = value
                    break
                cursor = cursor._next
                counter += 1

    #获取单链表的大小
    def mysize(self):
        counter = 0
        if self.root == None:
            return counter
        else:
            cursor = self.root
            while cursor != None:
                counter += 1
                cursor = cursor._next
            return counter

    #打印链表自身元素
    def myprint(self):
        if self.root == None:
            return
        else:
            cursor = self.root
            while cursor != None:
                print cursor.data
                cursor = cursor._next

if __name__ == '__main__':
    # 创建一个链表对象
    linklist = SingleLinkedList()
    #print lianbiao.isempty()
    linklist.append(7)
    linklist.append(3)
    linklist.append(4)
    linklist.append(6)
    linklist.append(5)
    linklist.append(6)
    linklist.append(7)
    linklist.append(3)
    #linklist.defDuplecate()
    #print linklist.mysize()
    #linklist.myprint()
    #print linklist.isempty()
    #print linklist.getvalue(5)
    #linklist.myprint()
    #print
    #linklist.updateNode(5, 9)
    #print linklist.pop()
    #linklist.delValue(5)
    #linklist.delNode(5)
    #linklist.prepend(9)
    #linklist.insert(5,9)
    #linklist.truncate()
    #print
    #linklist.myprint()
    #print linklist.getvalue(5)
