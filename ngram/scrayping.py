#!/usr/minoru/bin/anaconda3/bin/python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen
from urllib.parse import urlparse
from html.parser import HTMLParser
from struct import pack

# relative URL to absolute URL
def absURL(url):
	absurl = absURLInt(url)
	print("Try URL:" + absurl)
	return absurl

def absURLInt(url):
	o = urlparse(url)
	if o.netloc == "":
		if not url.startswith("/"):
			slash = "/"
		else:
			slash = ""
		return "https://www.teqstock.tokyo" + slash + url
	else:
		return url

# create &quot;a&quot; list
class AnchorList():
	def __init__(self):
		self.alist = []
		self.adic = {}

	def getURL(self, url):
		o = urlparse(url)
		if o.netloc == "" or o.netloc.startswith("www.teqstock.tokyo"):
			if o.path == "":
				return "/"
			else:
				return o.path
		else:
			return None


	def appendURL(self, url):
		rurl = self.getURL(url)
		if rurl is None:
			return
		if not rurl in self.adic:
			self.adic[rurl] = 0
			self.alist.append(rurl)

# strip HTML in plain tex
class StripperClass(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.anchors = AnchorList()
		self.title = ""
		self.body = ""
		self.inTitle = False
		self.inBody = False

	def handle_starttag(self, tag, attrs):
		if tag == 'a' or tag == 'A':
			for (aname, aval) in attrs:
				if aname == 'href':
					self.anchors.appendURL(aval)
		if tag == "title" or tag == "TITLE":
			self.inTitle = True
		if tag == "body" or tag == "BODY":
			self.inBody = True

	def handle_endtag(self, tag):
		if tag == "title" or tag == "TITLE":
			self.inTitle = False
		if tag == "body" or tag == "BODY":
			self.inBody = False

	def handle_data(self, data):
		if self.inTitle:
			self.title = data
		if self.inBody:
			self.body = self.body + data

# create fetch URL list
class Pass1():
	def __init__(self):
		self.alist = AnchorList()
		self.adict = {}

	def run1(self, url):
		st = StripperClass()
		absurl = absURL(url)
		with urlopen(absurl) as handle:
			r = handle.read()
			st.feed(r.decode('utf-8'))
			for a in st.anchors.alist:
				if a.find("blog") < 0:
					self.alist.appendURL(a)
			rurl = self.alist.getURL(url)
			self.alist.adic[rurl] = 1

	def nextURL(self):
		for url in self.alist.adic.keys():
			v = self.alist.adic[url]
			if v == 0:
				return url
		return None

	def run(self, url):
		rurl = self.alist.getURL(url)
		self.alist.appendURL(rurl)
		while True:
			nexturl = self.nextURL()
			if nexturl is None:
				break
			self.run1(nexturl)

class Pass2():
	def __init__(self):
		self.docoffset = 0
		self.chash = []
		# create hash table
		c = 0
		while c < 256:
			self.chash.append({})
			c = c + 1

	def myhash(self, c1, c2):
		n1 = ord(c1)
		n2 = ord(c2)
		return (n1 & 255) ^ ((n2 + 11) & 255)

	# write to the document file
	def writeDoc(self, handle, doc):
		d8 = doc.encode('utf-8')
		sd = pack('H', len(d8))
		handle.write(sd)
		handle.write(d8)
		return len(d8) + len(sd)

	def countH2Size(self, adic):
		count = 0
		for ak in adic.keys():
			count = count + 8
			count = count + 4 * len(adic[ak])
		count = count + 8 + 4
		return count

	def writeH2(self, h2, h):
		chsorted = sorted(h.keys())
		count = 0
		for ch in chsorted:
			adic = h[ch]
			csize = self.countH2Size(adic)
			ht = h2.tell()
			v = pack('I', csize)
			h2.write(v)
			v = pack('I', ord(ch[0]))
			h2.write(v)
			v = pack('I', ord(ch[1]))
			h2.write(v)
			count = count + 12
			akeys = sorted(adic.keys())
			for ak in akeys:
				aoffset = ak
				clist = adic[ak]
				itemLen = 4 * len(clist)
				v = pack('I', itemLen)
				h2.write(v)
				v = pack('I', aoffset)
				h2.write(v)
				for c in clist:
					v = pack('I', c)
					h2.write(v)
				count = count + itemLen + 8
			v = pack('I', 0)
			h2.write(v)
			if h2.tell() - ht != csize + 4:
				print("ht != c:" + str(h2.tell() - ht) + "," + str(csize + 4))
			count = count + 4
		v = pack('I', 0)
		h2.write(v)
		count = count + 4
		return count
			
	def writeHash(self, h1, h2):
		offset = 0
		c = 0
		for h in self.chash:
			vh = pack('I', offset)
			h1.write(vh)
			pos1 = h2.tell()
			if c == self.myhash('t', 'o'):
				print(str(c) + ":" + str(pos1))
			if pos1 != offset:
				print("pos1 != offset:" + str(pos1) + "," + str(offset))
			ow = self.writeH2(h2, h)
			pos2 = h2.tell()
			offset = offset + ow
			if pos2 - pos1 != ow:
				print("offset error:" + str(pos2 - pos1) + "," + str(ow))
			c = c + 1

	def createPage(self, tup):
		h = self.myhash(tup[0], tup[1])
		hs = self.chash[h]
		if not tup in hs.keys():
			hs[tup] = {}
		return hs[tup]
		
	def transpose(self, aoffset, body):
		c2 = ''
		count = 0
		for c in body:
			c1 = c2
			c2 = c
			if c1 != '':
				page = self.createPage((c1, c2))
				if not (aoffset in page.keys()):
					page[aoffset] = []
				page[aoffset].append(count)
			count = count + 1
				

	def run2(self, a, h1, h2, h3):
		with urlopen(absURL(a)) as h:
			r = h.read()
			s = StripperClass()

			# HTML を解析する
			s.feed(r.decode('utf-8'))
			title = s.title
			body = s.body
			aoffset = self.docoffset
			lenlink = self.writeDoc(h3, a)
			lentitle = self.writeDoc(h3, title)
			lenbody = self.writeDoc(h3, body)
			self.docoffset = self.docoffset + lenlink + lentitle + lenbody

			# 各文字について転置行列を作成する
			self.transpose(aoffset, body)

	def run1(self, pass1, h1, h2, h3):
		for a in pass1.alist.alist:
			self.run2(a, h1, h2, h3)
		self.writeHash(h1, h2)

	def run(self, pass1):
		with open("search_hash.bin", "wb") as h1:
			with open("search_classify.bin", "wb") as h2:
				with open("search_docs.bin", "wb") as h3:
					self.run1(pass1, h1, h2, h3)


# main program
pass1 = Pass1()
pass1.run('https://www.teqstock.tokyo/')
pass2 = Pass2()
pass2.run(pass1)
print(pass2.chash[pass2.myhash('t', 'o')])
