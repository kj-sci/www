#!/usr/bin/python

import sys
import re
import datetime
import ky_vars
import fetch_a_page

write = sys.stdout.write

# crawl all the pages in one website (base_url)
######################################################################
#                                                                    #
#                                                                    #
#                  Crawl a website                                   #
#                                                                    #
#                                                                    #
######################################################################
class crawl_a_site:
	######################################################################
	#                                                                    #
	#                                                                    #
	#                  Init Functions                                    #
	#                                                                    #
	#                                                                    #
	######################################################################
	def __init__(self, basedir, site_id, base_url):
		self.base_dir = basedir
		self.site_id = site_id

		self.flg_complete = 'N'
		
		self.ky_vars = ky_vars.ky_vars()
		
		# base url (e.g. http://www.yahoo.co.jp/)
		self.set_base_url(self.pretty_url(base_url))
		self.set_domain(self.extract_domain(self.base_url))

		# output files
		self.site_tree_fname = self.base_dir + '/' + 'site_tree_' + self.site_id + '.txt'
		self.page_data_fname = self.base_dir + '/' + 'page_data_' + self.site_id + '.txt'
		self.skip_url_fname = self.base_dir + '/' + 'skip_url_' + self.site_id + '.txt'
		self.url_list_fname = self.base_dir + '/' + 'page_id_url_list_' + self.site_id + '.txt'
		self.url_yet_to_visit_fname = self.base_dir + '/' + 'yet_to_visit_' + self.site_id + '.txt'
		self.link_data_fname = self.base_dir + '/' + 'link_data_'  + self.site_id + '.txt'

		self.fp_page_data = open(self.page_data_fname, 'w')
		
		# maximal depth for crawling (counting from the base_url)
		self.max_depth = 3

		self.init_site_data()

		self.page_hd = fetch_a_page.fetch_a_page()
		
		self.this_url_data = self.shift_url_queue()

		
	def init_site_data(self):
		######### Page Master Data ##########
		# page_id_to_node: page_id => node of the site_tree
		self.page_id_to_node = {}

		# url_to_node (url => [node1, node2, ...]
		self.url_to_node = {}

		########## MD5(contents) to page_node
		self.md5_to_node = {}
		
		########## Site Tree ############
		# root
		self.root = None
		
		self.url_queue = []

		self.page_id = 1
		self.push_url_queue(0, self.base_url, 0, 'ROOT')
		
		########## URL list outside of the site ############
		self.skip_url_list = {}
		
		
	def extract_domain(self, url):
		m = re.search('^[^/]*://([^/]*)/?', url)
		if m is not None:
			return m.group(1)
		else:
			sys.stderr.write('Error, cannot extract domain: url='+url+self.ky_vars.eol)
			return ''
	
	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Public Functions                                #
	#                                                                    #
	#                                                                    #
	######################################################################
	####### fetch a page data
	def fetch_a_page(self):
		res = 0
		if self.flg_complete == 'Y' or self.this_url_data is None:
			sys.stderr.write('No page url left\n')
			self.flg_complete = 'Y'
			return 0
		else:
			try:
				sys.stderr.write('=== '+str(self.page_id)+'-th page: Crawl '+self.this_url_data['url']+' ===\n')
			except:
				try:
					sys.stderr.write('=== '+str(self.page_id)+'-th page: Crawl '+self.this_url_data['url'].encode(self.ky_vars.outcode, 'ignore')+' ===\n')
				except:
					sys.stderr.write('=== '+str(self.page_id)+'-th page: Crawl xxx'+' ===\n')
					
			crawl_result = self.page_hd.fetch(self.this_url_data['url'])
			
			if crawl_result is None:
				try:
					sys.stderr.write("SKIP: Failed to fetch the page with URL: "+self.this_url_data['url']+"\n")
				except:
					try:
						sys.stderr.write("SKIP: Failed to fetch the page with URL: "+self.this_url_data['url'].encode(self.ky_vars.outcode, 'ignore')+"\n")
					except:
						sys.stderr.write("SKIP: Failed to fetch the page with URL: xxx"+"\n")
					
				if not self.skip_url_list.has_key(self.this_url_data['url']):
					self.skip_url_list[self.this_url_data['url']] = '#Fail# Failed to fetch the page'
				res = -1
			else:
				crawl_result['from_page_id'] = self.this_url_data['from_page_id']
				#crawl_result['url_prior'] = self.this_url_data['url']
				crawl_result['depth'] = self.this_url_data['depth']
				crawl_result['anchor_text'] = self.this_url_data['anchor_text']
				
				# debug
				#self.page_hd.print_vars_stderr()
				
				new_page_id = self.update_site_tree(crawl_result)
				
				if new_page_id > 0:
					# store page data:
					self.this_datetime = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
					self.fp_page_data.write('\n'+self.ky_vars.line_separator_1+'\n')
					self.fp_page_data.write('page_id:'+str(new_page_id)+'\n')
					self.fp_page_data.write('encoding:'+self.page_hd.outcode+'\n')
					self.fp_page_data.write('page_md5:'+crawl_result['page_md5']+'\n')
					try:
						self.fp_page_data.write('orig_url:'+crawl_result['orig_url']+'\n')
					except:
						try:
							self.fp_page_data.write('orig_url:'+crawl_result['orig_url'].encode(self.ky_vars.outcode, 'ignore')+'\n')
						except:
							self.fp_page_data.write('orig_url:ERR\n')

					try:
						self.fp_page_data.write('redirect_url:'+crawl_result['redirect_url']+'\n')
					except:
						try:
							self.fp_page_data.write('redirect_url:'+crawl_result['redirect_url'].encode(self.ky_vars.outcode, 'ignore')+'\n')
						except:
							self.fp_page_data.write('redirect_url:ERR\n')
						
					self.fp_page_data.write('datetime:'+self.this_datetime+'\n')
					self.fp_page_data.write(self.ky_vars.line_separator_2+'\n')
					self.page_hd.print_html(self.fp_page_data)
				res = 1
				
			self.this_url_data = self.shift_url_queue()
			
			return res


	####### add a page info to the site tree
	def update_site_tree(self, crawl_result):
		from_page_id = crawl_result['from_page_id']
		if from_page_id == 0:
			from_node = None
		else:
			from_node = self.page_id_to_node[from_page_id]

		page_md5 = crawl_result['page_md5']
		orig_url = crawl_result['orig_url']
		redirect_url = crawl_result['redirect_url']

		ret_val = 0
		##### if the page exists, ...
		if self.md5_to_node.has_key(page_md5):
			node = self.md5_to_node[page_md5]
			page_id = node['page_id']

			# link the node with parent_node
			self.update_node(page_id, node, from_node, crawl_result)
			#self.link_nodes(parent_page_id, parent_node, self.page_id, node)
			
			ret_val = -page_id
		
		else:
			##### if the page doesn't exist, ...
			# generate a new node
			this_page_id = self.page_id
			node = self.init_node(this_page_id, crawl_result)

			# link the node with parent node
			self.update_node(this_page_id, node, from_node, crawl_result)
			#self.link_nodes(parent_page_id, parent_node, this_page_id, node)
		
			# add urls to url_queue (may need to avoid crawling twice or more)
			next_depth = crawl_result['depth'] + 1
			if next_depth < self.max_depth:
				for url, anchor_text in crawl_result['link_to_urls'].items():
					if self.url_to_node.has_key(url):
						sys.stderr.write("SKIP: URL already visited: "+url+"\n")
					elif url[:-4:] == '.pdf':
						sys.stderr.write("SKIP: PDF file: "+url+"\n")
						if not self.skip_url_list.has_key(url):
							self.skip_url_list[url] = '#PDF#' + anchor_text
					elif re.search(self.domain, url):
						self.push_url_queue(this_page_id, url, next_depth, anchor_text)
					else:
						try:
							sys.stderr.write("SKIP: URL is not under the domain: "+url+"\n")
						except:
							sys.stderr.write("SKIP: URL is not under the domain.\n")
							
						if not self.skip_url_list.has_key(url):
							self.skip_url_list[url] = '#OUT#' + anchor_text
		
			# update hash tables
			self.page_id_to_node[this_page_id] = node
			self.md5_to_node[page_md5] = node
			
			ret_val = this_page_id
			self.page_id += 1
			
		self.url_to_node[crawl_result['orig_url']] = node
		self.url_to_node[crawl_result['redirect_url']] = node
		
		return ret_val

	######## print site info
	def print_site_tree(self):
		if self.root is None:
			return
			
		self.fp_site_tree = open(self.site_tree_fname, 'w')
		self.print_site_tree_header(self.fp_site_tree)
		self.doprint_site_tree(self.root, self.fp_site_tree)
		self.fp_site_tree.close()

	def print_link_data(self):
		if self.root is None:
			return
			
		self.fp_link_data = open(self.link_data_fname, 'w')
		self.print_link_data_header(self.fp_link_data)
		self.doprint_link_data(self.root, self.fp_link_data)
		self.fp_link_data.close()

	def print_url_list(self):
		if self.root is None:
			return
			
		self.fp_url_list = open(self.url_list_fname, 'w')
		self.print_url_list_header(self.fp_url_list)
		self.doprint_url_list(self.root, self.fp_url_list)
		self.fp_url_list.close()

		
	def exit(self):
		self.fp_page_data.close()
		
	def print_skip_url_list(self):
		if self.skip_url_list is None:
			return
			
		fp = open(self.skip_url_fname, 'w')

		# Header
		fp.write('URL')
		fp.write(self.ky_vars.outdelim)
		fp.write('ANCHOR_TEXT')
		fp.write('\n')

		for url, anchor_text in self.skip_url_list.items():
			try:
				fp.write(url.encode(self.ky_vars.outcode, 'ignore'))
			except:
				fp.write('ERR')
			fp.write(self.ky_vars.outdelim)
			try:
				fp.write(anchor_text.encode(self.ky_vars.outcode, 'ignore'))
			except:
				fp.write("ERR")
			fp.write('\n')
		
		fp.close()

	def print_url_yet_to_visit_list(self):
		fp = open(self.url_yet_to_visit_fname, 'w')

		# Header
		fp.write('URL')
		fp.write(self.ky_vars.outdelim)
		fp.write('PAGE_ID_FROM')
		fp.write(self.ky_vars.outdelim)
		fp.write('DEPTH')
		fp.write(self.ky_vars.outdelim)
		fp.write('ANCHOR_TEXT')
		fp.write('\n')

		for ptr in self.url_queue:
			fp.write(ptr['url'])
			fp.write(self.ky_vars.outdelim)
			fp.write(ptr['from_page_id'])
			fp.write(self.ky_vars.outdelim)
			fp.write(ptr['depth'])
			fp.write(self.ky_vars.outdelim)
			fp.write(ptr['anchor_text'])
			fp.write('\n')
		
		fp.close()

		
	######################################################################
	#                                                                    #
	#                                                                    #
	#                    Get/Set Functions                               #
	#                                                                    #
	#                                                                    #
	######################################################################
	
	def set_base_url(self, base_url):
		self.base_url = base_url
	
	def get_base_url(self):
		return self.base_url
	
	def set_domain(self, domain):
		self.domain = domain
		
	def get_domain(self):
		return self.domain
		
	def set_val_to_node(self, node, label, value):
		node[label] = value
	
	def get_val_from_node(self, node, label):
		if node.has_key(label):
			return node[label]
		else:
			return None

	def shift_url_queue(self):
		if len(self.url_queue) == 0:
			return None
		else:
			return self.url_queue.pop(0)
	
	# url: url_prior
	# depth: depth of this page(url)
	def push_url_queue(self, from_page_id, url, depth, anchor_text):
		dummy = {'from_page_id':from_page_id, 'url':url, 'depth':depth, 'anchor_text':anchor_text}
		self.url_queue.append(dummy)

	######################################################################
	#                                                                    #
	#                                                                    #
	#                 Other Help Functions                               #
	#                                                                    #
	#                                                                    #
	######################################################################
	def pretty_url(self, url):
		m = re.search('^[^/]*://[^/]*$', url)
		if m is not None:
			pretty_url = url + '/'
		else:
			pretty_url = url
		
		return pretty_url
		
			
	######## init_node
	# node:
	# - page_id (page_id corresponds to page_md5)
	# - title (<title> tag)
	# - anchor_text_list (text at an anchor link (<a href=...>anchor_text</a>)
	# - depth
	# - url_list (orig_url, redirect_url, ...)
	# - page_md5
	#
	# - link_from_ids (list)
	# - link_to_ids (list)
	# - flg_crawled (if child nodes are already crawled)
	# - flg_output (if already printed)
	def init_node(self, page_id, crawl_result):
		node = {}

		node['page_id'] = page_id
		node['parent_page_id'] = crawl_result['from_page_id']

		# md5 value of this page content (to compare dynamic pages)
		node['page_md5'] = crawl_result['page_md5']
		#node['parent_page_md5'] = None

		node['depth'] = crawl_result['depth']

		node['title'] = crawl_result['title']

		# url list
		dummy = {}
		dummy[crawl_result['orig_url']] = 1
		if crawl_result['orig_url'] != crawl_result['redirect_url']:
			dummy[crawl_result['redirect_url']] = 1
		node['url_list'] = dummy
		
		dummy1 = {}
		dummy1[crawl_result['anchor_text']] = 1
		node['anchor_text_list'] = dummy1
		
		# link(page_id) from other pages
		node['link_from_ids'] = {}

		# link(page_id) to other pages
		node['link_to_ids'] = {}
		
		node['flg_crawled'] = 'Y'
		node['flg_output'] = 'N'
		
		return node

	def update_node(self, this_page_id, this_node, from_node, crawl_result):
		# update depth, parent_page_id
		if this_node['depth'] > crawl_result['depth']:
			this_node['depth'] = crawl_result['depth']
			this_node['parent_page_id'] = crawul_result['from_page_id']
		
		# update url_list
		ptr = this_node['url_list']
		ptr[crawl_result['orig_url']] = 1
		ptr[crawl_result['redirect_url']] = 1
		
		# update anchor text
		ptr = this_node['anchor_text_list']
		ptr[crawl_result['anchor_text']] = 1

		if crawl_result['from_page_id'] != 0:
			# update link_from_ids
			ptr = this_node['link_from_ids']
			ptr[crawl_result['from_page_id']] = 1

			# update link_to_id (parent_node)
			ptr = from_node['link_to_ids']
			ptr[this_page_id] = 1
		else:
			self.root = this_node
	

	#def link_nodes(self, from_page_id, from_node, this_page_id, this_node):
	#	# if from_page_id exists (this_node is not "root")
	#	if from_page_id != 0:
	#		# set from_node info. to this_node
	#		link_from_ids = this_node['link_from_ids']
	#		#link_from_nodes = this_node['link_from_nodes']
	#		if not link_from_ids.has_key(from_page_id):
	#			link_from_ids[from_page_id] = 1
	#
	#		# add this_node to from_node
	#		link_to_ids = from_node['link_to_ids']
	#		if not link_to_ids.has_key(this_page_id):
	##	else:
	#		self.root = this_node
	
	######################################################################
	#                                                                    #
	#                                                                    #
	#                 Print Functions                                    #
	#                                                                    #
	#                                                                    #
	######################################################################
	def print_site_tree_header(self, fp):
		fp.write('depth')
		fp.write(self.ky_vars.outdelim)
		fp.write('page_id')
		fp.write(self.ky_vars.outdelim)
		fp.write('parent_page_id')
		fp.write(self.ky_vars.outdelim)
		fp.write('page_md5')
		fp.write(self.ky_vars.outdelim)
		fp.write('url')
		fp.write(self.ky_vars.outdelim)
		fp.write('#urls')
		fp.write(self.ky_vars.outdelim)
		fp.write('#anchor_text')
		fp.write(self.ky_vars.outdelim)
		fp.write('#links_from')
		fp.write(self.ky_vars.outdelim)
		fp.write('#links_to')
		fp.write(self.ky_vars.outdelim)
		fp.write('title')
		fp.write(self.ky_vars.outdelim)
		fp.write('anchor_text')
		fp.write('\n')
		
	def doprint_site_tree(self, node, fp):
		if node is None or node['flg_output'] == 'Y':
			return
		
		#if depth > node['depth']:
		#	return
			
		fp.write(str(node['depth']))
		fp.write(self.ky_vars.outdelim)

		fp.write(str(node['page_id']))
		fp.write(self.ky_vars.outdelim)

		fp.write(str(node['parent_page_id']))
		fp.write(self.ky_vars.outdelim)

		fp.write(node['page_md5'])
		fp.write(self.ky_vars.outdelim)

		for url in node['url_list'].keys():
			try:
				fp.write(url)
			except:
				try:
					fp.write(url.encode(self.ky_vars.outcode, 'ignore'))
				except:
					fp.write("ERR")
			fp.write(self.ky_vars.outdelim)
			break
		fp.write(self.ky_vars.outdelim)

		fp.write(str(len(node['url_list'].keys())))
		fp.write(self.ky_vars.outdelim)

		fp.write(str(len(node['anchor_text_list'].keys())))
		fp.write(self.ky_vars.outdelim)

		fp.write(str(len(node['link_from_ids'].keys())))
		fp.write(self.ky_vars.outdelim)

		fp.write(str(len(node['link_to_ids'].keys())))
		fp.write(self.ky_vars.outdelim)

		title = node['title']
		title = re.sub('\n', '<RET>', title)
		try:
			fp.write(title.encode(self.ky_vars.outcode, 'ignore'))
		except:
			try:
				fp.write(title)
			except:
				fp.write('ERR')
		fp.write(self.ky_vars.outdelim)

		for anchor_text in node['anchor_text_list']:
			anchor_text_1 = re.sub('\n', '<RET>', anchor_text)
			try:
				fp.write(anchor_text_1.encode(self.ky_vars.outcode, 'ignore'))
			except:
				try:
					fp.write(anchor_text_1)
				except:
					fp.write('ERR')

		fp.write(self.ky_vars.eol)
		
		node['flg_output'] = 'Y'
		
		for page_id in node['link_to_ids']:
			l = self.page_id_to_node[page_id]
			self.doprint_site_tree(l, fp)
		
	def print_link_data_header(self, fp):
		fp.write('from_page_id')
		fp.write(self.ky_vars.outdelim)
		fp.write('to_page_id')
		fp.write(self.ky_vars.eol)
	

	def doprint_link_data(self, node, fp):
		if node.has_key('flg_link'):
			return
		else:
			node['flg_link'] = 1
		
		page_id_from_str = str(node['page_id'])
		for page_id_to in node['link_to_ids'].keys():
			fp.write(page_id_from_str)
			fp.write(self.ky_vars.outdelim)
			fp.write(str(page_id_to))
			fp.write(self.ky_vars.eol)

		for page_id in node['link_to_ids']:
			l = self.page_id_to_node[page_id]
			self.doprint_link_data(l, fp)


	def print_url_list_header(self, fp):
		fp.write('page_id')
		fp.write(self.ky_vars.outdelim)
		fp.write('url')
		fp.write(self.ky_vars.eol)
	

	def doprint_url_list(self, node, fp):
		if node.has_key('flg_url_list'):
			return
		else:
			node['flg_url_list'] = 1

		page_id_str = str(node['page_id'])
		for url in node['url_list'].keys():
			fp.write(page_id_str)
			fp.write(self.ky_vars.outdelim)
			try:
				fp.write(url)
			except:
				try:
					fp.write(url.encode(self.ky_vars.outcode, 'ignore'))
				except:
					fp.write("ERR")
			fp.write(self.ky_vars.outdelim)
			fp.write(self.ky_vars.eol)

		for page_id in node['link_to_ids']:
			l = self.page_id_to_node[page_id]
			self.doprint_url_list(l, fp)

	
	######################################################################
	#                                                                    #
	#                                                                    #
	#                 Obsolete                                           #
	#                                                                    #
	#                                                                    #
	######################################################################

	# check if the page is already crawled (same url_current & md5)
	def is_page_duplicated(self, url, md5):
		if self.md5_to_node.has_key(md5) and self.url_to_node.has_key(url) and self.md5_to_node[md5] == self.url_to_node[url]:
			return 'Y'
		else:
			return 'N'


