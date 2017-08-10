#!/usr/bin/python

import sys
import re
#import urllib
import urllib2
#import codecs
import datetime
#import time
import hashlib
from BeautifulSoup import BeautifulSoup

import ky_vars

write = sys.stdout.write

######################################################################
#                                                                    #
#                                                                    #
#                  Fetch a webpage                                   #
#                                                                    #
#                                                                    #
######################################################################
class fetch_a_page:
	def __init__(self):
		self.ky_vars = ky_vars.ky_vars()

		self.raw_html = ''
		self.html = ''
		self.out_html = ''
		
	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Public Functions                                #
	#                                                                    #
	#                                                                    #
	######################################################################

	def fetch(self, orig_url):
		self.init_vars()
		
		self.set_orig_url(orig_url)
		self.set_orig_domain(self.extract_domain(orig_url))
		self.set_orig_base_url(self.extract_base_url(orig_url))
		
		#time.sleep(1)
		#sys.stderr.write("Access :"+orig_url+"\n")
		
		#if self.simple_get_html(0) is None:
		if self.simple_get_html_home(0) is None:
			return None
		
		# set self.page_md5
		self.calc_page_md5()
		
		# parse html
		self.extract_page_data()
		
		crawl_result = {}
		crawl_result['orig_url'] = self.orig_url
		crawl_result['orig_domain'] = self.orig_domain
		crawl_result['orig_base_url'] = self.orig_base_url
		crawl_result['redirect_url'] = self.redirect_url
		crawl_result['redirect_domain'] = self.redirect_domain
		crawl_result['redirect_base_url'] = self.redirect_base_url
		
		crawl_result['page_md5'] = self.page_md5
		crawl_result['title'] = self.title
		crawl_result['link_to_urls'] = self.links_url
		
		return crawl_result


	######################################################################
	#                                                                    #
	#                                                                    #
	#                Generic Help Functions                              #
	#                                                                    #
	#                                                                    #
	######################################################################
	def init_vars(self):
		self.html = ''
		self.orig_url = ''           # ex. http://www.yahoo.co.jp/r/dn
		self.redirect_url = ''       # ex. http://news.yahoo.co.jp/domestic/index.html

		self.orig_domain = ''        # ex. http://www.yahoo.co.jp
		self.redirect_domain = ''    # ex. http://news.yahoo.co.jp

		self.orig_base_url = ''      # ex. http://www.yahoo.co.jp/r/
		self.redirect_base_url = ''  # ex. http://news.yahoo.co.jp/domestic/
		
		self.page_md5 = None
		self.soup = None
		self.title = None
		self.links_url = {}
		

	def calc_page_md5(self):
		m = hashlib.md5()
		m.update(self.html.encode('utf_8', 'ignore'))
		self.page_md5 = m.hexdigest()

		return

	def extract_page_data(self):
		self.extract_title()
		# set self.links_url
		self.extract_links_url()

	def extract_title(self):
		l = self.soup.find('title')
		self.title = self.extract_str(l)

	def extract_links_url(self):
		### may need to add a feature for filtering out outside links
		#sys.stderr.write("in fetch_a_page:extract_links_url\n")
		
		#print "<========================= Page HTML =================================="
		#print self.html.encode('utf_8', 'ignore')
		#print "=======================================================================>"
		
		#sys.stderr.write("============== extract_links_url ======================\n")
		#sys.stderr.write(self.orig_url+' => '+self.redirect_url+"\n")
		#sys.stderr.write("=======================================================\n")
		
		links = self.soup.findAll('a')
		for l in links:
			if l.has_key('href'):
				url = self.get_abs_url(self.redirect_domain, self.redirect_base_url, self.redirect_url, l['href'])
				if url is not None:
					anchor_text = self.extract_str(l)
					self.links_url[url] = anchor_text

		frame_list = self.soup.findAll('frame')
		for l in frame_list:
			if l.has_key('src'):
				url = self.get_abs_url(self.redirect_domain, self.redirect_base_url, self.redirect_url, l['src'])
				if url is not None:
					anchor_text = 'NA(FRAME)'
					self.links_url[url] = anchor_text
		
		return

	def extract_str(self, tag):
		str = ''
		if tag is not None:
			for item in tag.contents:
				if item.string is not None:
					str += item.string.strip()
		
		return str

	def get_abs_url(self, domain, base_url, url, path_str):
		flg = 0
		path_str_bkup = path_str
		
		m = re.search('^javascript', path_str)
		if m is not None:
			path_str = self.extract_javascript_url(path_str)
		
		# case 1: absolute path
		if re.search('^http', path_str):
			abs_url = path_str
			flg = 1
		# case 2: starting with '/' (domain)
		else:
			m = re.search('^/+(.*)', path_str)
			if m is not None:
				path_str = m.group(1)
				abs_url = domain + '/' + path_str
				flg = 2
			else:
				# current_dir
				m = re.search('^\./+(.*)', path_str)
				if m is not None:
					path_str = m.group(1)
					abs_url = base_url + path_str
					flg = 3
				else:
					# parent_dir
					this_url = base_url
					this_path_str = path_str
					m = re.search('^\.\./+(.*)', this_path_str)
					
					if m is not None:
						while m is not None:
							this_path_str = m.group(1)
							m1 = re.search('^(.*/)[^/]*/$', this_url)

							if m1 is not None:
								this_url = m1.group(1)
								flg = 4
							else:
								#sys.stderr.write('Error in get_abs_url: base_url='+base_url+', path_str='+path_str+'\n')
								sys.stderr.write('Error in get_abs_url: flg = 5\n')
								abs_url = None
								flg = 5
								break

							m = re.search('^\.\./+(.*)', this_path_str)
						if flg == 4:
							#sys.stderr.write('parent dir(url ): '+base_url+'=>'+this_url+'\n')
							#sys.stderr.write('          (path): '+path_str+'=>'+this_path_str+'\n')
							abs_url = this_url + this_path_str
					else:
						if len(path_str) > 0 and path_str[0] == '#':
							abs_url = url + path_str
							flg = 6
						else:
							# other (current_dir)
							#sys.stderr.write('Warning in get_abs_url: path_str='+path_str+'\n')
							abs_url = base_url + path_str
							flg = 7

		abs_url = self.pretty_url(abs_url)

		#sys.stderr.write('('+str(flg)+") PATH: "+path_str_bkup+" => "+abs_url+"\n")

		return abs_url

	def extract_javascript_url(self, path_str):
		m = re.search('^javascript[^\'\"]*[\'\"]([^\'\"]*)[\'\"](.*)$', path_str)
		score = 0
		path_len = 0
		
		if m is not None:
			new_path_str = m.group(1)
			remainder = m.group(2)
			
			if len(new_path_str) >= 4 and new_path_str[:4] == 'http':
				score = 10
			elif len(new_path_str) >= 1 and new_path_str[0] == '/':
				score = 5
			elif len(new_path_str) >= 2 and new_path_str[:2] == './':
				score = 5
			elif len(new_path_str) >= 3 and new_path_str[:3] == '../':
				score = 5
			else:
				score = 1
			#sys.stderr.write("new_path_str="+new_path_str+", score="+str(score)+"\n")
			path_len = len(new_path_str)
			
			while True:
				m = re.search('^[^\'\"]*[\'\"]([^\'\"]*)[\'\"](.*)$', remainder)
				if m is not None:
					tmp_path_str = m.group(1)
					remainder = m.group(2)

					if len(tmp_path_str) >= 4 and tmp_path_str[:4] == 'http':
						tmp_score = 10
					elif len(tmp_path_str) >= 1 and tmp_path_str[0] == '/':
						tmp_score = 5
					elif len(tmp_path_str) >= 2 and tmp_path_str[:2] == './':
						tmp_score = 5
					elif len(tmp_path_str) >= 3 and tmp_path_str[:3] == '../':
						tmp_score = 5
					else:
						tmp_score = 1
					tmp_path_len = len(tmp_path_str)

					if tmp_score > score or (tmp_score == score and tmp_path_len > path_len):
						score = tmp_score
						path_len = tmp_path_len
						new_path_str = tmp_path_str
				else:
					break
			return new_path_str
		else:
			#sys.stderr.write('Error in extract_javascript_url, failed to extract url: path_str='+path_str+'\n')
			return ''
			

	def pretty_url(self, url):
		if url is None:
			return None
		
		m = re.search('^[^/]*://[^/]*$', url)
		if m is not None:
			pretty_url = url + '/'
		else:
			m = re.search('^(.*)#[^/]*$', url)
			if m is not None:
				pretty_url = m.group(1)
			else:
				pretty_url = url
		
		return pretty_url
			
	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Set Functions                                   #
	#                                                                    #
	#                                                                    #
	######################################################################

	def set_orig_url(self, url):
		self.orig_url = url

	def set_orig_domain(self, domain):
		self.orig_domain = domain

	def set_orig_base_url(self, url):
		self.orig_base_url = url

	def set_redirect_url(self, url):
		self.redirect_url = url

	def set_redirect_domain(self, domain):
		self.redirect_domain = domain
		
	def set_redirect_base_url(self, url):
		self.redirect_base_url = url

	def extract_domain(self, url):
		m = re.search('^([^/]*://[^/]*)', url)
		if m is not None:
			return m.group(1)
		else:
			sys.stderr.write('Error, cannot extract domain: url='+url.encode(self.ky_vars.outcode, 'ignore') + self.ky_vars.eol)
			return ''

	def extract_base_url(self, url):
		m = re.search('^(.*/)[^/]*$', url)
		if m is not None:
			return m.group(1)
		else:
			sys.stderr.write("Failed to extract base_url (url: "+url.encode(self.ky_vars.outcode, 'ignore') +"\n")
			return ''

	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Get HTML                                        #
	#                                                                    #
	#                                                                    #
	######################################################################


	def get_html_aig(self, num_steps):
		#time.sleep(3)

		proxy_str = self.ky_vars.win_id + ':' + self.ky_vars.win_pw + '@' + self.ky_vars.win_proxy
		
		flg = 'N'
		loop = 0
		sys.stderr.write("### In get_html\n")
		while flg == 'N' and loop < 5:
			try:
				proxy_support = urllib2.ProxyHandler({'http': proxy_str})
				opener = urllib2.build_opener(proxy_support)
				opener.addheaders = [('Accept', r'image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*'), ('Accept-Language', r'ja-JP'), ('User-Agent', r'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)'), ('Accept-Encoding', 'gzip, deflate')]

				req = urllib2.Request(self.orig_url)
				req.add_header("Accept-encoding", "gzip")
				#f = urllib2.urlopen(req)
				f = opener.open(req)

				self.chset_html = f.headers.getparam('charset')

				self.set_redirect_url(f.geturl())
				self.set_redirect_domain(self.extract_domain(self.redirect_url))
				self.set_redirect_base_url(self.extract_base_url(self.redirect_url))
				
				self.raw_html = f.read()
				if self.unicode_html(self.chset_html) == 0:
					sys.stderr.write('Failed to get html(1)\n')
					return None
				else:
					self.encode_html()
					
				#if f.headers.get('content-encoding', None) == 'gzip':
				#	self.html = gzip.GzipFile(fileobj=cStringIO.StringIO(self.html)).read()
				
				#self.html = unicode(self.html, self.ky_vars.incode)
				flg = 'Y'
				f.close()
			except urllib2.HTTPError, e:
				sys.stderr.write('The server couldn\'t fulfill the request.\n')
				sys.stderr.write('Error code: '+str(e.code)+"\n")
				#sys.stderr.write('Reason: '+str(e.reason)+"\n")
				if e.code == 404:
					self.html = None
					break
					
				time.sleep(self.ky_vars.sleep_time[loop])
				loop += 1
			except urllib2.URLError, e:
				sys.stderr.write('We failed to reach a server.'+'\n')
				#sys.stderr.write('Reason: '+e.reason+'\n')
				time.sleep(self.ky_vars.sleep_time[loop])
				loop += 1

		if self.html is None:
			sys.stderr.write('Failed to get html\n')
			return None
		else:
			sys.stderr.write('Successfully get html\n')
			try:
				self.soup = BeautifulSoup(self.html)
				if self.is_redirect() == 1:
					if num_steps <= 5:
						return self.get_html_aig(num_steps+1)
					else:
						return None
				return 1
			except:
				sys.stderr.write("Error: Failed to BeautifulSoup\n")
				return None

	def get_html_home(self, num_steps):
		#time.sleep(3)

		flg = 'N'
		loop = 0
		sys.stderr.write("### In get_html\n")
		while flg == 'N' and loop < 5:
			try:
				req = urllib2.Request(self.orig_url)
				#req.add_header("Accept-encoding", "gzip")				
				f = urllib2.urlopen(req)
				#f = opener.open(req)
				
				self.chset_html = f.headers.getparam('charset')

				self.set_redirect_url(f.geturl())
				self.set_redirect_domain(self.extract_domain(self.redirect_url))
				self.set_redirect_base_url(self.extract_base_url(self.redirect_url))
				
				self.raw_html = f.read()
				if self.unicode_html(self.chset_html) == 0:
					sys.stderr.write('Failed to get html(1)\n')
					return None
				else:
					self.encode_html()

				#if f.headers.get('content-encoding', None) == 'gzip':
				#	self.html = gzip.GzipFile(fileobj=cStringIO.StringIO(self.html)).read()
					
				#self.html = unicode(self.html, self.ky_vars.incode)
				flg = 'Y'
				f.close()
				
			except urllib2.HTTPError, e:
				sys.stderr.write('The server couldn\'t fulfill the request.\n')
				sys.stderr.write('Error code: '+str(e.code)+"\n")
				#sys.stderr.write('Reason: '+str(e.reason)+"\n")
				if e.code == 404:
					self.html = None
					break
					
				time.sleep(self.ky_vars.sleep_time[loop])
				loop += 1
			except urllib2.URLError, e:
				sys.stderr.write('We failed to reach a server.'+'\n')
				#sys.stderr.write('Reason: '+e.reason+'\n')
				time.sleep(self.ky_vars.sleep_time[loop])
				loop += 1

		if self.html is None:
			sys.stderr.write('Failed to get html\n')
			return None
		else:
			sys.stderr.write('Successfully get html\n')
			try:
				self.soup = BeautifulSoup(self.html)
				if self.is_redirect() == 1:
					if num_steps <= 5:
						return self.get_html_aig(num_steps+1)
					else:
						return None
				return 1
			except:
				sys.stderr.write("Error: Failed to BeautifulSoup\n")
				return None


	def simple_get_html(self, num_steps):
		#time.sleep(3)

		proxy_str = self.ky_vars.win_id + ':' + self.ky_vars.win_pw + '@' + self.ky_vars.win_proxy
		
		flg = 'N'
		loop = 0
		sys.stderr.write("### In get_html\n")
		proxy_support = urllib2.ProxyHandler({'http': proxy_str})
		opener = urllib2.build_opener(proxy_support)
		opener.addheaders = [('Accept', r'image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*'), ('Accept-Language', r'ja-JP'), ('User-Agent', r'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)'), ('Accept-Encoding', 'gzip, deflate')]

		try:
			req = urllib2.Request(self.orig_url)
			req.add_header("Accept-encoding", "gzip")				
			#f = urllib2.urlopen(req)
			f = opener.open(req)

			self.chset_html = f.headers.getparam('charset')
					
			self.set_redirect_url(f.geturl())
			self.set_redirect_domain(self.extract_domain(self.redirect_url))
			self.set_redirect_base_url(self.extract_base_url(self.redirect_url))
			
			self.raw_html = f.read()
			if self.unicode_html(self.chset_html) == 0:
				sys.stderr.write('Failed to get html(1)\n')
				return None
			else:
				self.encode_html()

			if f.headers.get('content-encoding', None) == 'gzip':
				self.html = gzip.GzipFile(fileobj=cStringIO.StringIO(self.html)).read()

			#self.html = unicode(self.html, self.ky_vars.incode)
			flg = 'Y'
			f.close()

			if self.html is None:
				sys.stderr.write('Failed to get html\n')
				return None
			else:
				sys.stderr.write('Successfully get html\n')
				self.soup = BeautifulSoup(self.html)
				if self.is_redirect() == 1:
					if num_steps <= 5:
						return self.get_html_aig(num_steps+1)
					else:
						return None
				return 1
		except:
			sys.stderr.write('simple_get_html: failed to fetch a page.'+'\n')
			return None
			

	def simple_get_html_home(self, num_steps):
		#time.sleep(1)

		flg = 'N'
		loop = 0
		sys.stderr.write("### In simple_get_html_home\n")

		try:
			req = urllib2.Request(self.orig_url)
			req.add_header("Accept-encoding", "gzip")				
			f = urllib2.urlopen(req)
			#f = opener.open(req)

			self.chset_html = f.headers.getparam('charset')
					
			self.set_redirect_url(f.geturl())
			self.set_redirect_domain(self.extract_domain(self.redirect_url))
			self.set_redirect_base_url(self.extract_base_url(self.redirect_url))
			
			self.raw_html = f.read()
			if self.unicode_html(self.chset_html) == 0:
				sys.stderr.write('Failed to get html(1)\n')
				return None
			else:
				self.encode_html()
				
			if f.headers.get('content-encoding', None) == 'gzip':
				self.html = gzip.GzipFile(fileobj=cStringIO.StringIO(self.html)).read()

			#self.html = unicode(self.html, self.ky_vars.incode)
			flg = 'Y'
			f.close()

			if self.html is None:
				sys.stderr.write('Failed to get html\n')
				return None
			else:
				sys.stderr.write('Successfully get html\n')
				self.soup = BeautifulSoup(self.html)
				if self.is_redirect() == 1:
					if num_steps <= 5:
						return self.get_html_aig(num_steps+1)
					else:
						return None
				return 1
		except urllib2.HTTPError, e:
			sys.stderr.write('HTTPError: The server couldn\'t fulfill the request.\n')
			sys.stderr.write('Error code: '+str(e.code)+"\n")
			#sys.stderr.write('Reason: '+str(e.reason)+"\n")
			if e.code == 404:
				self.html = None
			return None
		except urllib2.URLError, e:
			sys.stderr.write('URLError: failed to reach a server.'+'\n')
			#sys.stderr.write('Reason: '+e.reason+'\n')
			return None
		except:
			sys.stderr.write('Some Other Error: failed to fetch a page.'+'\n')
			return None
			
	def get_html_from_stdin(self):
		self.html = ''
		for line in sys.stdin:
			#self.html += line
			self.html += unicode(line, self.ky_vars.incode)

		self.set_redirect_url(self.orig_url)
		self.set_redirect_domain(self.orig_domain)
		self.set_redirect_base_url(self.orig_base_url)
		
		return 1


	def unicode_html(self, chset):
		if chset is not None:
			#sys.stderr.write("in unicode_html: charcode: "+chset+"\n")
			try:
				self.html = unicode(self.raw_html, chset)
			except:
				try:
					self.html = unicode(self.raw_html, 'cp932')
				except:
					try:
						self.html = unicode(self.raw_html, 'utf_8')
					except:
						try:
							self.html = unicode(self.raw_html, 'euc_jp')
						except:
							try:
								self.html = unicode(self.raw_html, 'iso2022_jp')
							except:
								sys.stderr.write("failed to unicode html(1)\n")
								return 0
		else:
			#sys.stderr.write("in unicode_html: no char code found\n")
			try:
				self.html = unicode(self.raw_html, 'cp932')
			except:
				try:
					self.html = unicode(self.raw_html, 'utf_8')
				except:
					try:
						self.html = unicode(self.raw_html, 'euc_jp')
					except:
						try:
							self.html = unicode(self.raw_html, 'iso2022_jp')
						except:
							sys.stderr.write("failed to unicode html(2)\n")
							return 0

		return 1

	def encode_html(self):
		try:
			self.out_html = self.html.encode(self.ky_vars.outcode)
			self.outcode = self.ky_vars.outcode
		except:
			if self.chset is not None:
				self.out_html = self.raw_html
				self.outcode = self.chset_html
			else:
				try:
					self.out_html = self.html.encode('utf_8')
					self.outcode = 'utf_8'
				except:
					try:
						self.out_html = self.html.encode('euc_jp')
						self.outcode = 'euc_jp'
					except:
						try:
							self.out_html = self.html.encode('iso2022_jp')
							self.outcode = 'iso2022_jp'
						except:
							self.out_html = self.raw_html
							self.outcode = '?'

	def is_redirect(self):
		tag_meta = self.soup.find('meta')
		for this_tag in tag_meta:
			if this_tag.has_key('http-equiv') and this_tag['http-equiv'] == 'refresh' and this_tab.has_key('url'):
				redirect_url = this_tag['url']
				if len(url) > 0:
					self.set_orig_url(redirect_url)
					self.set_orig_domain(self.extract_domain(redirect_url))
					self.set_orig_base_url(self.extract_base_url(redirect_url))
					return 1
		
		return 0
		
	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Get PDF                                         #
	#                                                                    #
	#                                                                    #
	######################################################################
	def tmp_get_pdf(self, pdf_fname):
		#time.sleep(3)

		proxy_str = self.ky_vars.win_id + ':' + self.ky_vars.win_pw + '@' + self.ky_vars.win_proxy
		
		sys.stderr.write("### In get_pdf\n")
		proxy_support = urllib2.ProxyHandler({'http': proxy_str})
		opener = urllib2.build_opener(proxy_support)
		opener.addheaders = [('Accept', r'image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*'), ('Accept-Language', r'ja-JP'), ('User-Agent', r'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)'), ('Accept-Encoding', 'gzip, deflate')]

		req = urllib2.Request(self.orig_url)
		#f = urllib2.urlopen(req)
		f = opener.open(req)
		
		fp_pdf = open(pdf_fname, 'wb')
		fp_pdf.write(f.read)

		fp_pdf.cloase()
		f.close()

		return 1



	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Output Functions                                #
	#                                                                    #
	#                                                                    #
	######################################################################
		
	def print_vars(self):
		print "=============== fetch_a_page: vars ==========================="
		print "orig_url: ", self.orig_url;
		print "orig_domain: ", self.orig_domain
		print "orig_base_url: ", self.orig_base_url;

		print "redirect_url: ", self.redirect_url
		print "redirect_domain: ", self.redirect_domain
		print "redirect_base_url: ", self.redirect_base_url
		
		#print "html: ", self.html
		print "page_md5: ", self.page_md5
		loop = 1
		print "Links:"
		for l in self.links_url.keys():
			print loop, ": ", l
			loop += 1
			
	def print_vars_stderr(self):
		sys.stderr.write("=============== fetch_a_page: vars ===========================\n")
		sys.stderr.write("orig_url: "+self.orig_url.encode(self.ky_vars.outcode, 'ignore')+"\n")
		sys.stderr.write("orig_domain: "+self.orig_domain.encode(self.ky_vars.outcode, 'ignore')+"\n")
		sys.stderr.write("orig_base_url: "+self.orig_base_url.encode(self.ky_vars.outcode, 'ignore')+"\n")

		sys.stderr.write("redirect_url: "+self.redirect_url.encode(self.ky_vars.outcode, 'ignore')+"\n")
		sys.stderr.write("redirect_domain: "+self.redirect_domain.encode(self.ky_vars.outcode, 'ignore')+"\n")
		sys.stderr.write("redirect_base_url: "+self.redirect_base_url.encode(self.ky_vars.outcode, 'ignore')+"\n")
		
		#sys.stderr.write("html: "+self.html+"\n")
		sys.stderr.write("page_md5: "+self.page_md5+"\n")
		loop = 1
		sys.stderr.write("Links:"+"\n")
		for l in self.links_url.keys():
			sys.stderr.write(str(loop)+": "+l+"\n")
			loop += 1

	def print_html(self, fp):
		#fp.write(self.html.encode(self.ky_vars.outcode, 'ignore'))
		fp.write(self.out_html)
	


