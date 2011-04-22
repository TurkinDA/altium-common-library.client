#-*- coding: utf-8 -*-

from PyQt4 import QtCore
from PyQt4 import QtGui

from kernel import abstract
from kernel import wrapper

##################################

class PyMainWindow(abstract.QWindow):

	def refresh(self):
		wrapper.refresh_view(self)

	def rewire(self):
		""" подключение сигналов """
		self.newButton.clicked.connect(self.on_new_button_clicked)
		self.editButton.clicked.connect(self.on_edit_button_clicked)
		self.saveButton.clicked.connect(self.on_save_button_clicked)
		self.cancelButton.clicked.connect(self.on_cancel_button_clicked)

		self.symbolButton.clicked.connect(self.on_symbol_button_clicked)
		self.packageButton.clicked.connect(self.on_package_button_clicked)
		self.modelButton.clicked.connect(self.on_model_button_clicked)

		self.componentList.currentItemChanged.connect(self.on_component_changed)

		wrapper.prepare_view(self)


	# обработчики сигналов
	def on_component_changed(self, current, previous):
		if current:
			self.editButton.setEnabled(True)
			wrapper.show_component_properties(self, current)

		else:
			self.editButton.setEnabled(False)

	# componentButton
	def on_new_button_clicked(self):
		wrapper.create_component(self)

	def on_edit_button_clicked(self):
		wrapper.edit_component(self)

	def on_save_button_clicked(self):
		wrapper.save_component(self)

	def on_cancel_button_clicked(self):
		wrapper.cancel_component(self)


	def on_component_created(self):
		print 'new component'
		wrapper.refresh_view(self)


	# symbolButton
	def on_symbol_button_clicked(self):
		dialog = SymbolManager('ui/symbol.ui', self)
#		dialog.setObjectName('Symbol Manager')
		dialog.accepted.connect(self.on_symbol_dialog_accept, QtCore.Qt.QueuedConnection)
		print 'SYMBOLS AGAIN', self.symbols
		dialog.load(self.symbols)
		dialog.show()

	def on_symbol_dialog_accept(self, data=None):
		print data


	# packageButton
	def on_package_button_clicked(self):
		dialog = PackageManager('ui/package.ui', self)
#		dialog.setObjectName('Package Manager')
		dialog.accepted.connect(self.on_package_dialog_accept, QtCore.Qt.QueuedConnection)
		dialog.load(self.packages)
		dialog.show()

	def on_package_dialog_accept(self, *args):
		print args
		print 'package manager accepted'


	# modelButton

	def on_model_button_clicked(self):
		dialog = ModelManager('ui/model.ui', self)
#		dialog.setObjectName('Model Manager')
		dialog.accepted.connect(self.on_model_dialog_accept, QtCore.Qt.QueuedConnection)
		dialog.load(self.models)
		dialog.show()

	def on_model_dialog_accept(self, data=None):
		print 'model manager says:', data



	# exportButton

	@QtCore.pyqtSlot()
	def on_export_button_clicked(self):
		wrapper.sync(self)



	@QtCore.pyqtSlot('PyQt_PyObject')
	def on_exportButton_respond(self, data=None):
		wrapper.export_respond(self, data)

	# downloadButton

	@QtCore.pyqtSlot()
	def on_downloadButton_clicked(self):
		wrapper.download_start(self)

	@QtCore.pyqtSlot('PyQt_PyObject')
	def on_downloadButton_respond(self, data=None):
		wrapper.download_respond(self, data)

	# uploadButton

	@QtCore.pyqtSlot()
	def on_uploadButton_clicked(self):
		wrapper.upload_start(self)

	@QtCore.pyqtSlot('PyQt_PyObject')
	def on_uploadButton_respond(self, data=None):
		wrapper.upload_respond(self, data)




class ComponentWizard(abstract.QDialog):

	def init(self):
		pass
#		self.worker = wrapper.PackageWorker()
#		self.worker.load()

	# okButton

	@QtCore.pyqtSlot()
	def on__clicked(self):
		print 'OK'

	@QtCore.pyqtSlot('PyQt_PyObject')
	def on_rejected(self, data=None):
		print 'Cancel'


	def load(self, components={}):
		""" загрузка начальных значений """
		manufacturers = []

		for component in components:
			manufacturers.append(components[component].manufacturer())

		manufacturers = list(set(manufacturers))
		manufacturers.sort()
		manufacturers.insert(0, ' ')

		self.manufacturerBox.addItems(manufacturers)


class PackageManager(abstract.QDialog):

#	def rewire(self):
#		self.worker = wrapper.PackageWorker()
#		self.worker.load()

	def success(self):
		print 'generating Package XML'
		self.accepted.emit('new package appeared')

	def load(self, packages={}):
		self.packages = packages

		packs = packages.keys()
		packs.sort()

		self.packageList.addItems(packs)



class SymbolManager(abstract.QDialog):

	def success(self):
		print 'generating Symbol XML'
		self.accepted.emit('new symbol appeared')

	def load(self, items={}):
		self.items = items

		items = items.keys()
		items.sort()

		self.symbolList.addItems(items)

class ModelManager(abstract.QDialog):

	def success(self):
		print 'generating Model XML'
		self.accepted.emit('new model appeared')

	def load(self, items={}):
		self.items = items

		unsorted = items.keys()
		sorted = unsorted.sort()

		self.modelList.addItems(sorted)
