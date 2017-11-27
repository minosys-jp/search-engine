#!/usr/minoru/bin/anaconda3/bin/python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import urljoin
from html.parser import HTMLParser
from struct import pack
from re import match

# h2 structure
# {hash('a', 'b'): {('a', 'b'): (docid, pr), ... }}
def contract(path):
	m = match("^(http|https)://([A-Za-z0-9._\-]+)(.*)", path)
	if m is None:
		return path
	mg = m.groups()
	s = mg[2].split("/")
	sj = []
	for si in s:
		if si == "..":
			sj.pop()
		elif si != "." and si != "":
			sj.append(si)
	path = "/".join(sj)
	if not path.startswith("/"):
		path = "/" + path
	sz = mg[0] + "://" + mg[1] + path
	return sz
	

def getDirectory(path):
	m = match("^(http|https)://([A-Za-z0-9._\-]+)(.*)", path)
	if m is None:
		return path
	mg = m.groups()
	s = mg[2].split("/")
	sj = []
	for si in s:
		if si == "..":
			sj.pop()
		elif si != "." and si != "":
			if si.find(".") < 0 and si.find("#") < 0:
				sj.append(si)
	path = "/".join(sj)
	if not path.startswith("/"):
		path = "/" + path
	sz = mg[0] + "://" + mg[1] + path
	return sz

def getFilePart(path):
	while path.endswith("/"):
		path = path[0:len(path) - 1]
	r = path.rfind("/")
	if r >= 0:
		path = path[r+1:]
	if path is None:
		path = ""
	return path

def getURL(last, rurl):
	if rurl.startswith("https://") or rurl.startswith("http://"):
		return rurl
	d = getDirectory(last)
	if d.endswith("/"):
		d = d[:len(d) - 1]
	if rurl.startswith("/"):
		rurl = rurl[1:]
	url = d + "/" + rurl
	url = contract(url)
	return url

# create &quot;a&quot; list
class AnchorList():
	def __init__(self):
		self.alist = []
		self.adic = {}

	def appendURL(self, url):
		if not url in self.adic:
			self.adic[url] = 0
			self.alist.append(url)

# strip HTML in plain tex
class StripperClass(HTMLParser):
	def __init__(self, baseURL):
		HTMLParser.__init__(self)
		self.anchors = AnchorList()
		self.title = ""
		self.body = ""
		self.inTitle = False
		self.inBody = False
		self.baseURL = baseURL
		self.parsed = urlparse(baseURL)

	def handle_starttag(self, tag, attrs):
		if tag == 'a' or tag == 'A':
			for (aname, aval) in attrs:
				if aname == 'href':
					ref = getURL(self.baseURL, aval)
					o = urlparse(ref)
					if o.netloc == self.parsed.netloc:
						self.anchors.appendURL(ref)
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
		self.parsed = None

	def canAppend(self, a):
		if a is None:
			return False
		if not a.endswith(".html"):
			return False
		if a.find("blog") >= 0:
			return False
		o = urlparse(a)
		if o.netloc != self.parsed.netloc:
			return False
		return True

	def run1(self, url):
		print("run1:" + url)
		st = StripperClass(url)
		with urlopen(url) as handle:
			r = handle.read()
			st.feed(r.decode('utf-8'))
			for a in st.anchors.alist:
				if self.canAppend(a):
					abspath = getURL(url, a)
					self.alist.appendURL(abspath)
			self.alist.adic[url] = 1

	def nextURL(self):
		for url in self.alist.adic.keys():
			v = self.alist.adic[url]
			if v == 0:
				return url
		return None

	def run(self, url):
		self.alist.appendURL(url)
		self.parsed = urlparse(url)
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
		count = 8 * len(adic)
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
				v = pack('I', aoffset)
				h2.write(v)
				v = pack('f', adic[ak])
				h2.write(v)
				count = count + 8
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
		for h in self.chash:
			vh = pack('I', offset)
			h1.write(vh)
			pos1 = h2.tell()
			if pos1 != offset:
				print("pos1 != offset:" + str(pos1) + "," + str(offset))
			ow = self.writeH2(h2, h)
			pos2 = h2.tell()
			offset = offset + ow
			if pos2 - pos1 != ow:
				print("offset error:" + str(pos2 - pos1) + "," + str(ow))

	def createPage(self, tup):
		h = self.myhash(tup[0], tup[1])
		hs = self.chash[h]
		if not tup in hs.keys():
			hs[tup] = {}
		return hs[tup]
		
	def calc_probability(self, aoffset, body):
		c2 = ''
		# pass1
		for c in body:
			c1 = c2
			c2 = c
			if c1 != '':
				page = self.createPage((c1, c2))
				if not (aoffset in page.keys()):
					page[aoffset] = 0
				page[aoffset] = page[aoffset] + 1
		lenbody1 = len(body) - 1
		# pass2
		c2 = ''
		for c in body:
			c1 = c2
			c2 = c
			if c1 != '':
				page = self.createPage((c1, c2))
				page[aoffset] = page[aoffset] / lenbody1

	def run2(self, pass1, a, h1, h2, h3):
		with urlopen(a) as h:
			r = h.read()
			s = StripperClass(a)

			# HTML を解析する
			s.feed(r.decode('utf-8'))
			title = s.title
			body = s.body
			aoffset = self.docoffset
			lenlink = self.writeDoc(h3, a)
			lentitle = self.writeDoc(h3, title)
			lenbody = self.writeDoc(h3, body)
			self.docoffset = self.docoffset + lenlink + lentitle + lenbody

			# 文字セットの出現確率を求める
			self.calc_probability(aoffset, body)

	def run1(self, pass1, h1, h2, h3):
		for a in pass1.alist.alist:
			if a is not None:
				self.run2(pass1, a, h1, h2, h3)
		self.writeHash(h1, h2)

	def run(self, pass1):
		with open("search_ngprob_hash.bin", "wb") as h1:
			with open("search_ngprob_classify.bin", "wb") as h2:
				with open("search_ngprob_docs.bin", "wb") as h3:
					self.run1(pass1, h1, h2, h3)


# main program
pass1 = Pass1()
pass1.run('https://www.teqstock.tokyo')
print("*** pass1 passed")
pass2 = Pass2()
pass2.run(pass1)
print(pass2.chash[pass2.myhash('t', 'o')])
