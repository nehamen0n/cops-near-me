"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import math
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, jsonify
import logging
from random import randint, randrange
from datetime import datetime, timezone

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#cop
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "mro2131"
DATABASE_PASSWRD = "307652"
DATABASE_HOST = "35.212.75.104" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
	
usernum= {}
@app.route('/')
def login():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


	#
	# example of a database query
	#
	
	#select_query = "SELECT location_name FROM Post"
	#cursor = g.conn.execute(text(select_query))
	#locations = []
	#for result in cursor:
		#locations.append(result[2])
	#cursor.close()
	#print(locations)

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	#context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("login.html")


@app.route('/login', methods=['GET','POST'])
def unumber():
	global usernum
	json_data = request.get_json()
	unum = json_data
	usernum = json_data['phonenumber']

    # Check if the phone number exists in the database
	select_query = "SELECT user_id FROM Users WHERE user_id = :usernum"
	result = g.conn.execute(text(select_query), {'usernum': usernum}).fetchone()

    # If the phone number doesn't exist, insert a new row
	if not result:
		add_query = "INSERT INTO Users (user_id, latitude, longitude, credibility) VALUES (:usernum, NULL, NULL, 'Y')"
		g.conn.execute(text(add_query), {'usernum': usernum})
		g.conn.commit()
	return jsonify(json_data=json_data)
   

@app.route('/userlocation')
def userlocation():
	return render_template('userlocation.html', usernum=usernum)

@app.route('/save_location', methods=['GET','POST'])
def savelocation():
	global usernum
	json_data = request.get_json()

	# get the type of post selected by the user + lat, long + radius
	post_type = json_data['postType']
	userlong = json_data['userlong']
	userlat = json_data['userlat']
	radius = json_data['radius']
	show_precinct=json_data['showPrecincts']

	update_query = "UPDATE Users SET latitude = :userlat, longitude = :userlong WHERE user_id = :unum"
	g.conn.execute(text(update_query), {'userlat': userlat, 'userlong': userlong, 'unum': usernum})
	g.conn.commit()

	if show_precinct ==true:
		precinct_query = "SELECT "
	

	# define dictionary of potential types of sql queries
	post_queries = {
		# combo of both 'SIGHTING' and 'SUBWAY'
        'Post': "SELECT P.latitude, P.longitude, P.location_name, P.description, P.date_reported, P.date_resolved, 'SIGHTING' AS post_type, S.cop_number, S.type_of_cop FROM Post P JOIN Sighting S ON P.post_id = S.post_id WHERE P.visible = 'Y' UNION SELECT P.latitude, P.longitude, P.location_name, P.description, P.date_reported, P.date_resolved, 'SUBWAY' AS post_type, NULL AS cop_number, SS.color_visibility FROM Post P JOIN Subway_Station SS ON P.location_name = SS.subway_station_name WHERE P.visible = 'Y'",
		# 'SIGHTING'
        'Sighting': "SELECT P.latitude, P.longitude, P.location_name, P.description, P.date_reported, P.date_resolved, 'SIGHTING' AS post_type, S.cop_number, S.type_of_cop FROM Post P JOIN Sighting S ON P.post_id = S.post_id WHERE P.visible = 'Y'",
		# 'SUBWAY'
        'Subway': "SELECT P.latitude, P.longitude, P.location_name, P.description, P.date_reported, P.date_resolved, 'SUBWAY' AS post_type, SS.subway_station_name, SS.color_visibility FROM Post P JOIN Subway_Station SS ON P.location_name = SS.subway_station_name WHERE P.visible = 'Y'"
    }

	# retrieve specific sql query
	select_query = post_queries.get(post_type)
	print(post_type)

	cursor = g.conn.execute(text(select_query))

	locations = {}
	currlocationid=0
	for result in cursor:
		location_name = result[2]
		latitude, longitude = result[0], result[1]
		

		# calculate distance to see what needs to be visible
		distance = haversine(userlat, userlong, latitude, longitude)
		if distance <= radius:
			temp={
				'id': currlocationid,
				'postlat': latitude,
				'postlong': longitude,
				'location_name': location_name,
				'description':result[3],
				'date_reported':result[4],
				'date_resolved':result[5],
				'post_type': result[6]
			}
			locations.update({currlocationid:temp})
			currlocationid+=1	
		
	cursor.close()
	return jsonify(locations = locations)
	
def haversine(lat1, long1, lat2, long2):
    import math

    # Radius of earth in miles
    R = 3959
    # Converting latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    long1 = math.radians(long1)
    lat2 = math.radians(lat2)
    long2 = math.radians(long2)

    # Calculating the difference
    dlon = long2 - long1
    dlat = lat2 - lat1

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate distance
    distance = R * c
    return distance

@app.route('/modcheck')
def modcheck():
	global usernum

	perms_query="SELECT user_id FROM Moderator WHERE perms = 'Y'"
	result = g.conn.execute(text(perms_query), {'usernum': usernum})
	print(result)
	#perm = uery user num in mod table to see if user has mod permissions (y/n).
	perm='Y'
	if perm == 'Y':
		return render_template('moderator.html')
	else:
		return render_template('reject.html')

@app.route('/modgen',methods=['GET','POST'])
def modgen():
	# run uery to get all posts, and make dictionary of all posts
	data={} # delete, send back all posts back to front end
	return jsonify(data=data)

@app.route('/add_location')
def add_location():
	return render_template('useradd.html', usernum=usernum)

@app.route('/add_post',methods=['GET','POST'])
def add_post():
	global usernum
	json_data = request.get_json()
	location_name=json_data['locationName']
	address=json_data['address']
	description=json_data['description']
	numberOfCops=json_data['numberOfCops']
	typeOfCops=json_data['typeOfCops']
	postlat=json_data['postlat']
	postlong=json_data['postlong']
	post_id= str(random_with_N_digits(8))
	post_type=json_data['post_type']

	check_query=  "SELECT post_id FROM Post WHERE post_id = :post_id"
	result = g.conn.execute(text(check_query), {'post_id': post_id}).fetchone()

	while result:
		post_id= random_with_N_digits(8)
		result = g.conn.execute(text(check_query), {'post_id': post_id}).fetchone()

	add_query = "INSERT INTO Post (post_id, latitude, longitude, location_name, address, date_reported, date_resolved, visible, description, user_id) VALUES (:post_id, :postlat, :postlong, :location_name, :address, now(), NULL, 'Y', :description, :user_id)"
	g.conn.execute(text(add_query), {'post_id': post_id, 'postlat': postlat, 'postlong':postlong,'location_name':location_name,'address':address,'description':description, 'user_id': usernum})
	g.conn.commit()

	if post_type == 'Sighting':
		sight_query= "INSERT INTO Sighting (post_id, user_id, cop_number, type_of_cop) VALUES (:post_id, :user_id, :cop_number, :type_of_cop)"
		g.conn.execute(text(sight_query), {'post_id': post_id, 'user_id': usernum, 'cop_number': numberOfCops,'type_of_cop':typeOfCops})
		g.conn.commit()
	else:
		sub_query= "INSERT INTO Subway_Post (post_id, user_id, cop_number) VALUES (:post_id, :user_id, :cop_number)"
		g.conn.execute(text(sight_query), {'post_id': post_id, 'user_id': usernum, 'cop_number': numberOfCops})
		g.conn.commit()

	
	

	return jsonify(json_data=json_data)



#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
