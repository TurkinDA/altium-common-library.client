#-*- coding: utf-8 -*-

import time
import datetime

from kernel import database
from kernel import utils
from kernel import objects
from kernel import transport

from modules import csvfile
from modules import msaccess

###########################


def application_start(application):
	database = db.Database(application.dbname)
	database.init()





def do_put_process(parent, data):

	result = data.id()

#	print 'PUT', result

	db = database.Database('data/pyclient.db')

	try:
		db.set_element(data)
		db.commit()

	except Exception, e:
		print 'Error:', e

#	print db.cursor.execute('SELECT * FROM components').fetchall()

	db.close()

	return result




def do_upload(worker, data=None):

	db = database.Database('data/pyclient.db')

	data = db.get_upload()

	if not data:
		return 'Nothing to upload'

	application = worker.parent()

	tr = transport.Transport(worker.parent())

	request = objects.RequestMessage('identify')
	request.add_value('login', application.settings.option('ACCOUNT', 'login', u'user'))
	request.add_value('password', application.settings.option('ACCOUNT', 'password', u'user'))
	xmlrequest = request.build()

	xmlresponse = tr.send(xmlrequest, 'http://altiumlib.noxius.ru/?page=client&rem=read')

	response = objects.ResponseMessage(xmlresponse)
	response.parse()

	if response.error:
		print response.error
		return 'Parsing answer Error'

	if response.type == 'error':
		try:
			message = response.values['message']
		except:
			message = 'General Error'

		return message

	sessionid = response.values['sessionid']

	# формирование XML
	request = objects.RequestMessage('set_components')
	request.add_value('sessionid', sessionid)

	for element in data:
		request.add_item(element)

	xmlrequest = request.build()

	print xmlrequest

	# отправка XML
	application = worker.parent()
	xmlresponse = tr.send(xmlrequest, 'http://altiumlib.noxius.ru/?page=client&rem=read&PHPSESSID=' + sessionid)

	# отмечаем отправленные компоненты
#	for element in answer:
#		db.set_sent(element)

	db.commit()
	db.close()

	return 'Uploaded %d components' % (len(data),)


def do_download(worker, data):
	# загрузка обновлений с сервера

	application = worker.parent()
	tr = transport.Transport(worker.parent())

#	sessionid = application.settings.option('CONNECTION', 'sessionid')

	try:
		application.sessionid

	except AttributeError:
		request = objects.RequestMessage('identify')
		request.add_value('login', application.settings.option('ACCOUNT', 'login', u'user'))
		request.add_value('password', application.settings.option('ACCOUNT', 'password', u'user'))
		xmlrequest = request.build()

		xmlresponse = tr.send(xmlrequest, 'http://altiumlib.noxius.ru/?page=client&rem=read')

		print xmlresponse
		if not xmlresponse:
			return 'Communication error'

		response = objects.ResponseMessage(xmlresponse)
		response.parse()

		if response.error:
			print response.error
			return 'Parsing error'

		if response.type == 'error':
			try:
				message = response.values['message']
			except:
				message = 'General Error'

			return message

#		application.settings.set_option('CONNECTION', 'sessionid', sessionid)
		application.sessionid = response.values['sessionid']

	since = application.settings.option('DATA', 'lastupdate', datetime.datetime.min)

	request = objects.RequestMessage('get_components')
	request.add_value('sessionid', application.sessionid)
	request.add_value('since', since)

	xmlrequest = request.build()

	xmlresponse = tr.send(xmlrequest, 'http://altiumlib.noxius.ru/?page=client&rem=read&PHPSESSID=' + application.sessionid)

	if not xmlresponse:
		return 'Communication error'

	response = objects.ResponseMessage(xmlresponse)
	response.parse()

	if response.type == 'error':
		print 'Error parsing response:', response.error
		return 'Error parsing response'

	application.settings.set_option('DATA', 'lastupdate', datetime.datetime.utcnow()	.isoformat(' '))

	if not response.data:
		print 'No data fetched'
		return 'Downloaded %d new components' % (len(response.data),)

	db = database.Database('data\pyclient.db')

	for element in response.data:
		db.set_element(element, sent=True)

	db.commit()
	db.close()

	return 'Downloaded %d new components' % (len(response.data),)


def do_export(parent, data):
	# обновление пользовательских источников данных

	db = database.Database('data/pyclient.db')

	for category in systemcategories:
		print 'CATEGORY:', category

		content = db.export(category)

		# костыль для полей Author локальных элементов
		for element in content:
			element['Author'] = element.get('Author', parent.parent().settings.option('ACCOUNT', 'user'))

		print 'content', content
		result = sortupdate(category, content)

		if result:
			table, fieldlist, sorted = result

			print 'sorted', sorted

#			tr = csvfile.CSVWriter()
			tr = msaccess.MDBWriter()
			tr.initialize()

			if tr.error:
				print 'ERROR'
				return tr.error

			tr.set(table, fieldlist, sorted)

			if tr.error:
				print 'ERROR', tr.error
				return tr.error

#			db.set_exported(category, content)
			db.commit()

	db.close()

	return 'Done'


def sortupdate(category, data):
	if not data:
		print 'nothing to sort'
		return

	print 'processing'
	cfg = utils.OptionManager('data.ini')

	if cfg.error:
		print cfg.error
		return

	# наименование таблицы для текущей категории
	table = cfg.option('TABLES', category)

	if not table:
		print 'no table %s' % (category,)
		return

	# dict наименования полей таблицы и их значения
	tablefields = cfg.options(table + '_FIELDS', True) or {} # or DEFAULTS {'Part Number': '[Manufacturer].[PartNumber]', 'Library Ref': '[SymbolLib]', 'Footprint Ref': '[FootprintLib]'}


	if not tablefields:
		print 'no fields in %s' % (table,)
		return

	content = []

	def stringize(s):

#		print s
		if isinstance(s, datetime.datetime):
			return s.isoformat(' ')

		elif isinstance(s, bool) or isinstance(s, int) or isinstance(s, float):
			return str(s)

		elif s is None:
			return ''

		else:
			return s



	for element in data:
		dataout = {}

		### причесать, очень коряво ###
		for field in tablefields.keys():
			value = tablefields[field]

			# тут отделяются поля которые относятся к datetime (их нельзя комбинировать с другими)
			if value in [''.join(( '{', s, '}' )) for s in element.keys()]:
				value = element[value[1:-1]] or None # заменяется на значение параметра с тем же типом

			else:
				#надо так: для каждой подстроки в скобочках [] заменить на строковое значение параметра
				for parameter in element.keys():
					value = value.replace(''.join(('[', parameter, ']')), stringize(element[parameter]) or '')

			dataout[field] = value

		content.append(dataout)

	
	print 'done'

	fieldlist = tuple(tablefields.keys())

	print fieldlist

	return table, fieldlist, content








def dosmthng(parent, *args, **kwargs):
	print kwargs
	i = 0
	while i < 16:
		print i
		parent.iter(i)
		i = i + 1
		time.sleep(0.2)


#####################

systemcategories = {
	'A': 'Устройства (общее обозначение)',
	'B': 'Преобразователи неэлектрических величин в электрические (кроме генераторов и источников питания) или наоборот',
	'C': 'Конденсаторы',
	'D': 'Схемы интегральные, микросборки',
	'DA': 'Схема интегральные, аналоговые',
	'E': '',
	'F': '',
	'G': '',
	'H': '',
	'K': '',
	'L': '',
	'R': '',
	'VD': '',
}


