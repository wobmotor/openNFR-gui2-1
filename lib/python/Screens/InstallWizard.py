from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigBoolean, getConfigListEntry, ConfigSelection, ConfigYesNo, ConfigIP
from Components.Network import iNetwork
from Components.Ipkg import IpkgComponent
from Plugins.Extensions.Infopanel.PluginWizard import PluginInstall
from enigma import eDVBDB
import os
from Screens.Console import Console

config.misc.installwizard = ConfigSubsection()
config.misc.installwizard.hasnetwork = ConfigBoolean(default = False)
config.misc.installwizard.ipkgloaded = ConfigBoolean(default = False)
config.misc.installwizard.channellistdownloaded = ConfigBoolean(default = False)


class InstallWizard(Screen, ConfigListScreen):

	STATE_UPDATE = 0
	STATE_CHOISE_CHANNELLIST = 1

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
                print "installwizard starts"
		self.index = args
		self.list = []
		ConfigListScreen.__init__(self, self.list)

		if self.index == self.STATE_UPDATE:
			config.misc.installwizard.hasnetwork.value = False
			config.misc.installwizard.ipkgloaded.value = False
			modes = {0: " "}
			self.enabled = ConfigSelection(choices = modes, default = 0)
			self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getAdapterList()]
			is_found = False
			if os.path.isfile("/tmp/netwizardselection"):
			        f = open('/tmp/netwizardselection', 'r')
			        adapx1 = f.read()
			        f.close()
			        adapx1 = adapx1.replace('\n','')
                        	print "adapx1:", adapx1
                        else:
				adapx1 = 'eth0'
                                print "adapx1+1:", adapx1
			for x in self.adapters:
				if adapx1 == 'eth0':
					if iNetwork.getAdapterAttribute(adapx1, 'up'):
						self.ipConfigEntry = ConfigIP(default = iNetwork.getAdapterAttribute(adapx1, "ip"))
						iNetwork.checkNetworkState(self.checkNetworkCB)
						if_found = True
					else:
						iNetwork.restartNetwork(self.checkNetworkLinkCB)
					break
				elif adapx1 == 'wlan0':
					if iNetwork.getAdapterAttribute(adapx1, 'up'):
						self.ipConfigEntry = ConfigIP(default = iNetwork.getAdapterAttribute(adapx1, "ip"))
						iNetwork.checkNetworkState(self.checkNetworkCB)
						if_found = True
					else:
						iNetwork.restartNetwork(self.checkNetworkLinkCB)
					break
				elif adapx1 == 'ra0':
					if iNetwork.getAdapterAttribute(adapx1, 'up'):
						self.ipConfigEntry = ConfigIP(default = iNetwork.getAdapterAttribute(adapx1, "ip"))
						iNetwork.checkNetworkState(self.checkNetworkCB)
						if_found = True
					else:
						iNetwork.restartNetwork(self.checkNetworkLinkCB)
					break
			if is_found is False:
				self.createMenu()
		elif self.index == self.STATE_CHOISE_CHANNELLIST:
			self.enabled = ConfigYesNo(default = True)
			modes = {"default": _("OpenNFR List"),"scan": _("scan new")}
			self.channellist_type = ConfigSelection(choices = modes, default = "default")
			self.createMenu()

	def checkNetworkCB(self, data):
		if data < 3:
			config.misc.installwizard.hasnetwork.value = True
		self.createMenu()

	def checkNetworkLinkCB(self, retval):
		if retval:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		else:
			self.createMenu()

	def createMenu(self):
		try:
			test = self.index
		except:
			return
		self.list = []
		if self.index == self.STATE_CHOISE_CHANNELLIST:
			self.list.append(getConfigListEntry(_("Channel list type"), self.channellist_type))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		if self.index == 0:
			return
		ConfigListScreen.keyLeft(self)
		self.createMenu()

	def keyRight(self):
		if self.index == 0:
			return
		ConfigListScreen.keyRight(self)
		self.createMenu()

	def run(self):
		if self.index == self.STATE_CHOISE_CHANNELLIST and self.enabled.value and self.channellist_type.value == "scan":
			os.system("rm /etc/enigma2/*.tv")
			os.system("rm /etc/enigma2/*.radio")
			config.misc.installwizard.channellistdownloaded.value = False
			os.system("tar -xzf /etc/channel.tar.gz -C /etc/enigma2")
			eDVBDB.getInstance().reloadServicelist()
			eDVBDB.getInstance().reloadBouquets()
		else:
			cmd = "opkg update && opkg install --force-reinstall opennfr-settings;"
			self.session.open(Console, title = _("Please wait configuring OpenNFR Channellist"), cmdlist = [cmd], finishedCallback = self.reloadPlugin, closeOnSuccess = True)
		return

	def reloadPlugin(self):
		eDVBDB.getInstance().reloadServicelist()
		eDVBDB.getInstance().reloadBouquets()
		return
class InstallWizardIpkgUpdater(Screen):
	def __init__(self, session, index, info, cmd, pkg = None):
		Screen.__init__(self, session)

		self["statusbar"] = StaticText(info)

		self.pkg = pkg
		self.index = index
		self.state = 0

		self.ipkg = IpkgComponent()
		self.ipkg.addCallback(self.ipkgCallback)

		if self.index == InstallWizard.STATE_CHOISE_CHANNELLIST:
			self.ipkg.startCmd(cmd, {'package': 'enigma2-plugin-settings-*'})
		else:
			self.ipkg.startCmd(cmd, pkg)

	def ipkgCallback(self, event, param):
		if event == IpkgComponent.EVENT_DONE:
			if self.index == InstallWizard.STATE_UPDATE:
				config.misc.installwizard.ipkgloaded.value = True
			elif self.index == InstallWizard.STATE_CHOISE_CHANNELLIST:
				if self.state == 0:
					self.ipkg.startCmd(IpkgComponent.CMD_INSTALL, self.pkg)
					self.state = 1
					return
				else:
					config.misc.installwizard.channellistdownloaded.value = False
					eDVBDB.getInstance().reloadBouquets()
					eDVBDB.getInstance().reloadServicelist()
			self.close()
