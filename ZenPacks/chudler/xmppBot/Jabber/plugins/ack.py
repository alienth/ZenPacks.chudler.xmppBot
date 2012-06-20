"""Acknowledge Zenoss events by their EventID"""

from Jabber.Plugins import Plugin
from Jabber.Options import Options
from optparse import OptionError
import transaction

class Ack(Plugin):

  name = 'ack'
  capabilities = ['ack', 'acknowledge', 'help']
  minseverity = 4
  private = False

  def call(self, args, log, client, sender, messageType, **kw):

    log.debug('Alert Ack plugin running with arguments: %s' % args)


    opts = self.options()

    # parse the options
    try:
        (options, arguments) = opts.parse_args(args)
        log.debug('Done parsing arguments.  Options are "%s", arguments expanded to %s' % (options, arguments))
    except OptionError, message:
        client.sendMessage(str(message), sender, messageType)
        return False

    if options.eventIds is None and options.device is None and not options.all and not arguments:
        message = 'must specify --all, -d, or event id list'
        client.sendMessage(message, sender, messageType)
        return False

    if arguments and options.eventIds is None and options.device is None and not options.all:
        idsToAck = arguments

    if options.eventIds:
        idsToAck = options.eventIds.lower().split(',')


    # we will build this list of matching eventids, then ack them using acknowledge()
    acking = []

    if options.all:
        log.debug('User has requested to ack all events.')
        for event in self.adapter.events():
            if event.severity < self.minseverity:
                continue
            acking.append(event.evid)
            log.debug('Queuing %s event to ack.' % event.evid)
        return self.acknowledge(client, options.test, options.verbose, acking, sender, messageType, log)

    if options.device:
        log.debug('User has requested to ack all events for device %s.' % options.device)
        for event in self.adapter.events():
            if event.severity < self.minseverity:
                continue
            if event.device == options.device:
                acking.append(event.evid)
                log.debug('Queuing %s event to ack.' % event.evid)
        return self.acknowledge(client, options.test, options.verbose, acking, sender, messageType, log)

    for event in self.adapter.events():
        # python 2.5 will accept tuple instead of this.
        for idToAck in idsToAck:
            if event.severity < self.minseverity:
                continue
            eventid = event.evid
            log.debug('Checking if eventid %s is one to ack (%s)' % (eventid, idToAck))
            if eventid.lower().startswith(idToAck) or eventid.lower().endswith(idToAck):
                log.debug('We should ack this event: %s.  It will be queued' % eventid)
                acking.append(eventid)

    if len(acking) > 1:
        message = 'ambiguous results; please be more specific'
        client.sendMessage(str(message), sender, messageType)
        return False
    elif len(acking) == 1:
        return self.acknowledge(client, options.test, options.verbose, acking, sender, messageType, log)
    else:
        message = 'Sorry.  Found no events to acknowledge.'
        client.sendMessage(str(message), sender, messageType)
        return False

  def acknowledge(self, client, dryrun, verbose, events, sender, messageType, log):
        if dryrun:
            log.debug('Test mode is activated, so events will not be acknowledged.')
            message = 'Test mode: %d WOULD have been acknowledged.' % len(events)
            client.sendMessage(str(message), sender, messageType)

        else:
            log.debug('Acking all queued events.')
            zenUser = self.findUser(sender)
            self.adapter.ackEvents(zenUser, events)
            log.debug('Done Acking all queued events.')
            transaction.commit()
            message = 'Acknowledged %d' % len(events)
            client.sendMessage(message, sender, messageType)

        if verbose:
            message += '\n'
            message += ', '.join(events)
            client.sendMessage(message, sender, messageType)

  def findUser(self, sender):

        # remove the resource from the sender
        if '/' in sender:
            sender = sender.split('/')[0]


        for user in self.adapter.userSettings():
            try:
                jabberProperty = user.getProperty('JabberId').lower()
                if jabberProperty == sender:
                        return user.id
            except AttributeError:
                pass

        return sender

  def options(self):
    parser = Options(description = 'Acknowledge events by eventid', prog = 'ack')
    parser.add_option('-e', '--eventids', dest='eventIds', help='Complete or partial eventids to ack.  Ids can be sepratated by commas.  Partial ids can match either the beginning or end of the eventid.')
    parser.add_option('--all', dest='all', action='store_true', default=False, help='Acknowledge all events.  If -e is also specified, it will still acknowledge every event.')
    parser.add_option('-d', '--device', dest='device', help='Only ack events that exist on this device.')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Send list of all acknowledged events.  Can be noisy.  USE WITH CAUTION.')
    parser.add_option('-t', '--test', dest='test', action='store_true', default=False, help='Do not acknowledge events, but show what would be done.  Works with -v.')
    return parser

  def help(self):
    opts = self.options()
    return str(opts.help())
