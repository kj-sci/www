#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ky_vars:
	def __init__(self):
		# orcl
		self.orcl_id = ''
		self.orcl_pw = ''
		self.orcl_tns = 'orcl'

		# win
		self.win_id = ''
		self.win_pw = ''
		self.win_proxy = '170.105.225.130:8080'
		
		self.indelim = '\t'
		self.outdelim = '\t'
		self.eol = '\n'
		
		self.incode = 'cp932'
		#self.outcode = 'cp932'
		self.outcode = 'utf_8'
		
		self.sleep_time = [60, 180, 300, 600, 1200, 1800, 3600]
		
		self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		self.http_header = { 'User-Agent' : self.user_agent }
		self.http_values = {'name' : 'Michael Foord',
          'location' : 'Northampton',
          'language' : 'Python' }
		
		
		#self.line_separator_1 = '############################## fce54f6594e19a2c1e426548d40508ec ##############################'
		#self.line_separator_2 = '############################## 159afb14ff76e0e47f2acc8e9143c487 ##############################'
		
		self.line_separator_1 = '############################## fce54f6594e19a2c1e426548d40508ecr23498yjoerj ##############################'
		self.line_separator_2 = '############################## 159afb14ff76e0e47f2acc8e9143c487aoseijafhald ##############################'

	def get_var(self, var_name):
		if var_name == 'orcl_id':
			return self.orcl_id
		elif var_name == 'orcl_pw':
			return self.orcl_pw
		elif var_name == 'orcl_tns':
			return self.orcl_tns
		else:
			return 'NA'

	