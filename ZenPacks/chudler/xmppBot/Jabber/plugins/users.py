"""Check if the sender is a valid zenoss admin.  For access control"""

from Jabber.Plugins import Plugin
from Jabber.Options import Options
from optparse import OptionError

class Users(Plugin):

  name = 'users'
  capabilities = ['users', 'zenusers', 'help']
  private = False

  def call(self, args, log, client, sender, messageType, **kw):
    log.debug('Users plugin running with arguments %s' % args)
    # TODO switch this to optparse and make sure help works.
    users = []
    message = 'No Users'
    haveUser = False

    for user in self.adapter.userSettings():
        haveUser = True
        try:
            jabberId = user.getProperty('JabberId') or 'No JabberId'
        except AttributeError:
            jabberId = 'No JabberId'
        users.append('%s (%s)' % (user.id, jabberId))
    if haveUser:
        message = '\n'.join(users)

    client.sendMessage(message, sender, messageType)


  def help(self):
    return """
usage users
    List current users and their Jabber ID.  Takes no arguments.
"""
