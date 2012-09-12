 
###    This program is free software: you can redistribute it and/or modify
###    it under the terms of the GNU General Public License as published by
###    the Free Software Foundation, either version 3 of the License, or
###    (at your option) any later version.
###
###    This program is distributed in the hope that it will be useful,
###    but WITHOUT ANY WARRANTY; without even the implied warranty of
###    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
###    GNU General Public License for more details.

###    You should have received a copy of the GNU General Public License
###    along with this program.  If not, see <http://www.gnu.org/licenses/>.

##   Android Python script (SL4A) to alert (email only at moment) @untappd user
##   of the beers nearby on their wishlist.

##   Probably just alpha quality and dev release as you have to edit in your @untappd
##   dev key (and login and email addr) at the top of the script. Tested under
##   SL4A Python 2.6 and Android 4.0.

##   Usage: just run it under SL4A and it will chug away for a few secs and then
##   request the user to pick a mail client. Pick one and hit send. Note with
##   'verbose=True' lots of info to SL4A terminal.

##   Props
##     * Original gps/geo code from PipeMan.
##     * Untappd API wrapper orig from xavier@santolaria.net (see copyright/perms below).
##     * misc Python hints and utilities like uniqfy() found via Goog

##   Happy beer triangulating,
##   @gaak99
##   Spring 2012


import android, math, sys
from time import sleep

## change these per user
UNTAPPD_DEVKEY = ''
#UNTAPPD_DEVKEY = 'deadbeef' #test post fail
UNTAPPD_LOGIN = ""
EMAIL_ADDR = ""

## misc parameters might be worth changing
NEARBY_RADIUS = 15 #Radius==1==1k feet
HOURS_PAST = 160 #discard beer check-ins after this many hours
GPS_SLEEP = 10  #sleep this many seconds to sync w/GPS

##debug flag
verbose = True #tty logging

VERSION = 0.332 #alpha
if verbose:
	print "Starting (Version ", VERSION, ") ..."

# Android setup
droid = android.Android()

def get_location():
	droid.startLocating()
	sleep(GPS_SLEEP)
	location = droid.readLocation().result
	droid.stopLocating()
#if not location: #this is useless btw
#	print "Get location fail"
#	raise SystemExit

	try:
		gps = location['gps']
		if gps is None:
			if verbose:
				print "gps is None, try Network loca bro ..."
			gps = location['network']
		if verbose:
			print "lat=", gps['latitude'], "long=", gps['longitude'];
		return gps
	except:
		e = sys.exc_info()[1]
		if verbose:
			print "get location fail: ", e
		droid.makeToast("get location fail: " + e)
		exit(1)
	
#calculate the distance between two gps locations
#		Radius==1==1k feet
def distance(lat1, lng1, location2, radius = NEARBY_RADIUS):
	R = 6371
	latitude1 = math.radians(lat1)
	latitude2 = math.radians(location2['latitude'])
	longitude1 = math.radians(lng1)
	longitude2 = math.radians(location2['longitude'])
	distance = math.acos(math.sin(latitude1) * math.sin(latitude2) + \
			     math.cos(latitude1) * math.cos(latitude2) *\
			     math.cos(longitude2-longitude1)) * R
	if distance < radius:
		return True, distance
	else:
		return False, distance

# untappd.com API support
import httplib, urllib, json, datetime

"""
untappd.py - v0.1

Python wrapper for the Untappd API - http://untappd.com/api/docs


Copyright (c) 2011 Xavier Santolaria <xavier@santolaria.net>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
class untapped_API:
	def __init__(self, apikey, uname, pw):
		self.fqdn = 'api.untappd.com'
		self.apikey = apikey
		self.user = uname
		self.password = pw
		self.post_total = 0

	def post_total():
		return self.post_total
	
	def post(self, post):
		if verbose and self.post_total == 99:
			print "post start: WARNING post total at 99 yo!"
		params = urllib.urlencode({'key': UNTAPPD_DEVKEY}) #needed ??
		headers = {"Content-type": "application/x-www-form-urlencoded", 
			   "Accept": "text/plain"} 
		conn = httplib.HTTPConnection(self.fqdn)
		conn.request("POST", post, params, headers)
		response = conn.getresponse()
		self.post_total += 1
		if response.status != 200:
			if verbose:
				print "http post fail: ", response.status, ": ", response.reason
			return response.status, response.reason, []
		rawdata = response.read() 
		conn.close()
		return 200, response.reason, json.loads(rawdata)

	def beer_checkins(self, beer_id, offset):
		return self.post("/v3/beer_checkins?key=" + self.apikey \
			        + "&bid=" + beer_id \
				+ "&offset=" + offset)

	def venue_checkins(self, venue):
		venue_id = UNTAPPD_VENUES[venue]
		return self.post("/v3/venue_checkins?key=" + self.apikey + \
				 "&venue_id=" + venue_id)

	def user_feed(self, uname):
		return self.post("/v3/user_feed?key=" + self.apikey + "&user=" + uname)

	def wishlist(self, uname, offset):
		return self.post("/v3/wish_list?key=" + self.apikey \
				 + "&user=" + uname \
			         + "&offset=" + offset)

def uniqfy(seq):
	"""Returns List Without Duplicates Preserving the Original Order

	Removes the second and following duplicates in a sequence without
	altering the original order (in contrast to the builtin set type
	where ordering is not defined).

	@param seq sequence that my contain duplicates or not
	@return list without duplicates preserving the original order

	Usage
	-----
	>>> uniqfy([1, 2, 1, 1, 2, 3])
	[1, 2, 3]
	"""
	uniq = set(seq)
	return [item for item in seq if item in uniq and not uniq.remove(item)]

# Is beer checkin nearby & recentish?
def beerp(ci, beerl, location):
	#	print "beerp start: ci beer_id=", ci['beer_id']
	stopp = False
	date_creat = datetime.datetime.strptime(ci['created_at'], \
						'%a, %d %b %Y %H:%M:%S +0000')
	now = datetime.datetime.now()
	if (now - date_creat) < datetime.timedelta(hours=HOURS_PAST):
#		print "Recent brew..."
		hit, dis = distance(float(ci['venue_lat']), \
				    float(ci['venue_lng']), \
				    location)
		if hit:
			hit_str = ci['beer_name'] + "_@_" + ci['venue_name'] 
			print "Recent brew nearby!"
			beerl.append(hit_str)
	else:
		stopp = True
		print "old brew yo, stopping lookups for this beer"

#	print "beerp end: stopp=", stopp			
	return beerl, stopp

# fetch next set (25) of checkins for beer_id and see if they nearby&recent
def tap_untappd_beer_checkins(ut, beer_id, ci_offset, beerl, location):
#	print "tap...checkins start: beer_id=", beer_id, " ci_offset=", ci_offset
	status, reason, data = ut.beer_checkins(beer_id, str(ci_offset))
	if status != 200:
		if verbose:
			print "tap_untappd_beer_checkins http fail: stat: ", status
		if status == 501 and len(beerl) > 0:
			return 0, beerl, True
		droid.makeToast("beer checkins: http fail:" + str(status) + " " + reason)
		if status == 501:
			droid.makeToast("HTTP call limit exceeded. Try again later.")
		sleep(3)
		exit(3)
	ci_total = 0
	stopp = False
	for result in data['results']:
		ci_total = ci_total + 1
		if result['venue_id']:
			beerl, stopp = beerp(result, beerl, location)
			if stopp:
				break
		
#	print "tap...checkins end:  ci_total this page=", ci_total
	return ci_total, beerl, stopp

throttled = [] #xxx glob

# given a beer id, fetch all recent checkins
def all_checkins_beer_id(ut, beer_id, beer_name, beerl, location):
	ci_offset = 0
	total_beers = 0
	while True:
		ci_total, beerl, stopp = tap_untappd_beer_checkins(ut, beer_id, \
								   ci_offset, beerl, location)
		total_beers += ci_total
		if ci_total < 25 or stopp:
			break
		ci_offset += 25
		if ci_offset > 75: #??
			if verbose:
				print "all_beer_checkins: throttle this beer lookups..."
			throttled.append(beer_name)
			break
	if verbose:
		print "all_beer_checkins end: beer_id=", beer_id, \
		    " total checkins proced: ", total_beers
	return beerl

# fetch untappd wish list for uname and return list of nearby beers and wishlist totals
def tap_untappd(ut, uname, wl_offset, total_beers_uniq, location):
	if verbose:
		print "tap_untapped: start: wishlist offset=", wl_offset
	status, reason, data = ut.wishlist(uname, str(wl_offset))
	if status != 200:
		if verbose:
			print "tap_untapped http post fail", status
		if status == 501 and total_beers_uniq > 0: #too many calls/hr
			return 0, []
		droid.makeToast("wishlist: http fail: " + str(status) + " " + reason)
		if status == 501:
			droid.makeToast("HTTP call limit exceeded. Try again later.")
		sleep(3)
		exit(2)
	beerl = [] #main list of beers found nearby recently
	wl_total = 0
	for result in data['results']:
		wl_total = wl_total + 1
		beerl = all_checkins_beer_id(ut, result['beer_id'], \
					     result['beer_name'], beerl, location)
				
	if verbose:
		print "tap_untapped: end: wishlist total=", wl_total, " ", \
			"hit totes=", len(beerl), " ", beerl
	return wl_total, beerl

#given a list return string like "beer\nberr..."
def hit_list2str(l):
	if verbose:
		print "list2str: wishlist uniq hits totes=", len(l), " ", l
	str = ""
	if l is not None:
		for b in l:
			str = str + "\n" + b
	return str

# Return a string of nearby beers & stats found in @untappd db.
def nearby_beers(location):
	ut = untapped_API(UNTAPPD_DEVKEY, '', '')
	wl_offset = 0
	total_beers_uniq = 0
	wl_total = 0
	all_beers = "Wishlist beers nearby ...\n\n"
	while True:
		wl_pg_total, beers_list = tap_untappd(ut, UNTAPPD_LOGIN, wl_offset, \
						      total_beers_uniq, location)
		if len(beers_list) > 0:
			total_beers_uniq += len(uniqfy(beers_list))
			all_beers = all_beers + "\n" + hit_list2str(uniqfy(beers_list))
		if verbose:
			print "nearby_beers: http POST total=", ut.post_total
		wl_total += wl_pg_total
		if wl_pg_total < 25:
			break
		wl_offset += 25
	all_beers = all_beers \
		+ "\n\nOf " + str(wl_total) + " Wishlist beers " \
	        + str(total_beers_uniq) + " unique beer/bar combos found.\n\n" \
		+ str(ut.post_total) \
		+ " HTTP POST calls done (100(?) max allowed per hour by api.untappd.com).\n\n"
	if verbose:
		print "wl_total=", wl_total, " throttled=", throttled
	return all_beers

## main program
#droid.notify("@untappd wish granted! ", beer)
droid.sendEmail(EMAIL_ADDR, \
		"@untappd Wishlist Bro", \
		nearby_beers(get_location()))

if verbose:
	print "done."
