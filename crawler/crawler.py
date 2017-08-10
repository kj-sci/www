#!/usr/bin/python

import sys
import re
import os
import time

import ky_vars
import crawl_a_site
#import fetch_a_page

write = sys.stdout.write

######################################################################
#                                                                    #
#                                                                    #
#                        Main Module                                 #
#                                                                    #
#                                                                    #
######################################################################
def main():
	if len(sys.argv) < 2:
		sys.stderr.write('Usage: cat urllist | python crawler.py datadir\n')
		sys.exit(1)

	datadir = sys.argv[1]
	
	site_hd_list = []
	site_id_list = []
	site_url_list = []
	
	num_simul_run = 5
	
	sleep_sec = 2
	
	header = sys.stdin.readline()
	flg_eof = 'N'
	
	##### Get the first 5 urls
	loop = 0
	# input
	# 0: site_id
	# 1: site_url
	while loop < num_simul_run:
		line = sys.stdin.readline()
		if line:
			#sys.stderr.write(str(loop)+":\n")
			data = line[:-1].split('\t')
				
			site_id = data[0]
			site_url = data[1]

			if not (site_id == '2586' or site_id == '3887' or site_id == '3883' or site_id == '3894' or site_id == '3898' or int(site_id) > 3898):
				continue
				
			if not re.match('^http', site_url):
				site_url = 'http://'+site_url

			sys.stderr.write("######################################################\n")
			sys.stderr.write("##### REGISTER "+str(loop)+"-th url (ID:"+site_id+"): "+site_url+"#####\n")
			sys.stderr.write("######################################################\n")

			this_site_hd = crawl_a_site.crawl_a_site(datadir, site_id, site_url)
			site_hd_list.append(this_site_hd)
			site_id_list.append(site_id)
			site_url_list.append(site_url)

			loop += 1
		else:
			flg_eof = 'Y'
			break
			
	if flg_eof == 'Y':
		num_simul_run = loop
		
	###### Infinite loop
	# fetch pages until get to the end of pages
	# if fetched all pages, output, then load a new line
	while True:
		res = 0
		sys.stderr.write("========== fetch pages =============\n")
		for idx in range(num_simul_run):
			sys.stderr.write("fetch page (ID:"+site_id_list[idx]+"): "+site_url_list[idx]+"\n")
			this_res = site_hd_list[idx].fetch_a_page()

			if this_res == 0:  # no page left
				sys.stderr.write("crawling finished for "+site_url_list[idx]+"\n")
				# output site tree
				site_hd_list[idx].print_site_tree()
				site_hd_list[idx].print_link_data()
				site_hd_list[idx].print_url_list()
				site_hd_list[idx].print_skip_url_list()
				#site_hd_list[idx].print_url_yet_to_visit_list()
				site_hd_list[idx].exit()

				# read a new url
				if flg_eof == 'N' and not os.path.exists('stop.txt'): # not eof
					line = sys.stdin.readline()
					if line:
						data = line[:-1].split('\t')
						site_id = data[0]
						site_url = data[1]

						if not re.match('^http', site_url):
							site_url = 'http://'+site_url

						loop += 1
						sys.stderr.write("######################################################\n")
						sys.stderr.write("##### REGISTER "+str(loop)+"-th url (ID:"+site_id+"): "+site_url+"#####\n")
						sys.stderr.write("######################################################\n")

						this_site_hd = crawl_a_site.crawl_a_site(datadir, site_id, site_url)
						site_hd_list[idx] = this_site_hd
						site_id_list[idx] = site_id
						site_url_list[idx] = site_url
						
						res = 1
					else: #no page left
						flg_eof = 'Y'
			else:
				res = 1

		if res == 0:
			break

		sys.stderr.write("sleep\n")
		time.sleep(sleep_sec)


			
	
if __name__=='__main__':
	main()

