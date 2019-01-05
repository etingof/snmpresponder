#!/usr/bin/env python
#
# This file is part of snmpresponder software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpresponder/license.html
#
import os
import sys
import getopt
import traceback
import random
import re
import socket
from pysnmp.error import PySnmpError
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncore.dgram import udp
try:
    from pysnmp.carrier.asyncore.dgram import udp6
except ImportError:
    udp6 = None
try:
    from pysnmp.carrier.asyncore.dgram import unix
except ImportError:
    unix = None
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.proto import rfc1902, rfc1905
from pysnmp.proto.api import v2c
from pysnmp.smi import builder
from pysnmp.smi import instrum
from pysnmp.smi import compiler
from pysnmp.smi import error as smi_error
from pyasn1 import debug as pyasn1_debug
from pysnmp import debug as pysnmp_debug
from snmpresponder.error import SnmpResponderError
from snmpresponder import log, daemon, cparser, macro, endpoint
from snmpresponder.plugins.manager import PluginManager
from snmpresponder.plugins import status
from snmpresponder.lazylog import LazyLogString

PROGRAM_NAME = 'snmpresponder'
CONFIG_VERSION = '1'
PLUGIN_API_VERSION = 1
CONFIG_FILE = '/etc/snmpresponder/snmpresponderd.cfg'

authProtocols = {
  'MD5': config.usmHMACMD5AuthProtocol,
  'SHA': config.usmHMACSHAAuthProtocol,
  'SHA224': config.usmHMAC128SHA224AuthProtocol,
  'SHA256': config.usmHMAC192SHA256AuthProtocol,
  'SHA384': config.usmHMAC256SHA384AuthProtocol,
  'SHA512': config.usmHMAC384SHA512AuthProtocol,
  'NONE': config.usmNoAuthProtocol
}

privProtocols = {
  'DES': config.usmDESPrivProtocol,
  '3DES': config.usm3DESEDEPrivProtocol,
  'AES': config.usmAesCfb128Protocol,
  'AES128': config.usmAesCfb128Protocol,
  'AES192': config.usmAesCfb192Protocol,
  'AES192BLMT': config.usmAesBlumenthalCfb192Protocol,
  'AES256': config.usmAesCfb256Protocol,
  'AES256BLMT': config.usmAesBlumenthalCfb256Protocol,
  'NONE': config.usmNoPrivProtocol
}

snmpPduTypesMap = {
    rfc1905.GetRequestPDU.tagSet: 'GET',
    rfc1905.SetRequestPDU.tagSet: 'SET',
    rfc1905.GetNextRequestPDU.tagSet: 'GETNEXT',
    rfc1905.GetBulkRequestPDU.tagSet: 'GETBULK',
    rfc1905.ResponsePDU.tagSet: 'RESPONSE',
}


def main():

    class MibTreeProxyMixIn(object):

        MIB_INTRUMENTATION_CALL = None

        def _getMgmtFun(self, contextName):
            return self._routeToMibTree

        def _routeToMibTree(self, *varBinds, **context):

            cbFun = context['cbCtx']

            mibTreeReq = gCurrentRequestContext.copy()

            pdu = mibTreeReq['snmp-pdu']

            pluginIdList = mibTreeReq['plugins-list']

            logCtx = LogString(mibTreeReq)

            reqCtx = {}

            for pluginNum, pluginId in enumerate(pluginIdList):

                st, pdu = pluginManager.processCommandRequest(
                    pluginId, snmpEngine, pdu, mibTreeReq, reqCtx
                )

                if st == status.BREAK:
                    log.debug('plugin %s inhibits other plugins' % pluginId, ctx=logCtx)
                    pluginIdList = pluginIdList[:pluginNum]
                    break

                elif st == status.DROP:
                    log.debug('received SNMP message, plugin %s muted request' % pluginId, ctx=logCtx)
                    # TODO: need to report some special error to drop request
                    cbFun(varBinds, **context)
                    return

                elif st == status.RESPOND:
                    log.debug('received SNMP message, plugin %s forced immediate response' % pluginId, ctx=logCtx)
                    # TODO: should we respond something other than request?
                    cbFun(varBinds, **context)
                    return

            # Apply PDU to MIB(s)

            mibTreeId = mibTreeReq['mib-tree-id']
            if not mibTreeId:
                log.error('no matching MIB tree route for the request', ctx=logCtx)
                cbFun(varBinds, **dict(context, error=smi_error.GenError()))
                return

            mibInstrum = mibTreeIdMap.get(mibTreeId)
            if not mibInstrum:
                log.error('MIB tree ID %s does not exist', ctx=logCtx)
                cbFun(varBinds, **dict(context, error=smi_error.GenError()))
                return

            log.debug('received SNMP message, applied on mib-tree-id %s' % mibTreeId, ctx=logCtx)

            cbCtx = pluginIdList, mibTreeId, mibTreeReq, snmpEngine, reqCtx, context['cbFun']

            mgmtFun = getattr(mibInstrum, self.MIB_INTRUMENTATION_CALL)

            mgmtFun(*varBinds, **dict(context, cbFun=self._mibTreeCbFun, cbCtx=cbCtx, acFun=None))

        # TODO: it just occurred to me that `*varBinds` would look more consistent
        def _mibTreeCbFun(self, varBinds, **context):
            pluginIdList, mibTreeId, mibTreeReq, snmpEngine, reqCtx, cbFun = context['cbCtx']

            logCtx = LogString(mibTreeReq)

            err = context.get('error')
            if err:
                log.info('MIB operation resulted in error: %s' % err, ctx=logCtx)

            cbFun(varBinds, **dict(context, cbFun=cbFun))

            # plugins need to work at var-binds level
            #
            # for key in tuple(mibTreeRsp):
            #     pdu = mibTreeRsp['client-snmp-pdu']
            #
            #     for pluginId in pluginIdList:
            #         st, pdu = pluginManager.processCommandResponse(
            #             pluginId, snmpEngine, pdu, mibTreeReq, reqCtx
            #         )
            #
            #         if st == status.BREAK:
            #             log.debug('plugin %s inhibits other plugins' % pluginId, ctx=logCtx)
            #             break
            #         elif st == status.DROP:
            #             log.debug('plugin %s muted response' % pluginId, ctx=logCtx)
            #             self.releaseStateInformation(stateReference)
            #             return
            #
            #     try:
            #         self.sendPdu(snmpEngine, stateReference, pdu)
            #
            #     except PySnmpError:
            #         log.error('mibTree message #%s, SNMP response error: %s' % (msgId, sys.exc_info()[1]),
            #                   ctx=logCtx)
            #
            #     else:
            #         log.debug('received mibTree message #%s, forwarded as SNMP message' % msgId, ctx=logCtx)


    class GetCommandResponder(MibTreeProxyMixIn, cmdrsp.GetCommandResponder):
        MIB_INTRUMENTATION_CALL = 'readMibObjects'


    class GetNextCommandResponder(MibTreeProxyMixIn, cmdrsp.NextCommandResponder):
        MIB_INTRUMENTATION_CALL = 'readNextMibObjects'


    class GetBulkCommandResponder(MibTreeProxyMixIn, cmdrsp.BulkCommandResponder):
        MIB_INTRUMENTATION_CALL = 'readNextMibObjects'


    class SetCommandResponder(MibTreeProxyMixIn, cmdrsp.SetCommandResponder):
        MIB_INTRUMENTATION_CALL = 'writeMibObjects'


    class LogString(LazyLogString):

        GROUPINGS = [
            ['callflow-id'],
            ['snmp-engine-id',
             'snmp-transport-domain',
             'snmp-bind-address',
             'snmp-bind-port',
             'snmp-security-model',
             'snmp-security-level',
             'snmp-security-name',
             'snmp-credentials-id'],
            ['snmp-context-engine-id',
             'snmp-context-name',
             'snmp-context-id'],
            ['snmp-pdu',
             'snmp-content-id'],
            ['snmp-peer-address',
             'snmp-peer-port',
             'snmp-peer-id'],
            ['mib-tree-id'],
            ['client-snmp-pdu'],
        ]

        FORMATTERS = {
            'client-snmp-pdu': LazyLogString.prettyVarBinds,
            'snmp-pdu': LazyLogString.prettyVarBinds,
        }

    def securityAuditObserver(snmpEngine, execpoint, variables, cbCtx):
        securityModel = variables.get('securityModel', 0)

        logMsg = 'SNMPv%s auth failure' % securityModel
        logMsg += ' at %s:%s' % variables['transportAddress'].getLocalAddress()
        logMsg += ' from %s:%s' % variables['transportAddress']

        statusInformation = variables.get('statusInformation', {})

        if securityModel in (1, 2):
            logMsg += ' using snmp-community-name "%s"' % statusInformation.get('communityName', '?')
        elif securityModel == 3:
            logMsg += ' using snmp-usm-user "%s"' % statusInformation.get('msgUserName', '?')

        try:
            logMsg += ': %s' % statusInformation['errorIndication']

        except KeyError:
            pass

        log.error(logMsg)

    def usmRequestObserver(snmpEngine, execpoint, variables, cbCtx):

        mibTreeReq = {
            'snmp-security-engine-id': variables['securityEngineId']
        }

        cbCtx.clear()
        cbCtx.update(mibTreeReq)

    def requestObserver(snmpEngine, execpoint, variables, cbCtx):

        mibTreeReq = {
            'callflow-id': '%10.10x' % random.randint(0, 0xffffffffff),
            'snmp-engine-id': snmpEngine.snmpEngineID,
            'snmp-transport-domain': variables['transportDomain'],
            'snmp-peer-address': variables['transportAddress'][0],
            'snmp-peer-port': variables['transportAddress'][1],
            'snmp-bind-address': variables['transportAddress'].getLocalAddress()[0],
            'snmp-bind-port': variables['transportAddress'].getLocalAddress()[1],
            'snmp-security-model': variables['securityModel'],
            'snmp-security-level': variables['securityLevel'],
            'snmp-security-name': variables['securityName'],
            'snmp-context-engine-id': variables['contextEngineId'],
            'snmp-context-name': variables['contextName'],
        }

        try:
            mibTreeReq['snmp-security-engine-id'] = cbCtx.pop('snmp-security-engine-id')

        except KeyError:
            # SNMPv1/v2c
            mibTreeReq['snmp-security-engine-id'] = mibTreeReq['snmp-engine-id']

        mibTreeReq['snmp-credentials-id'] = macro.expandMacro(
            credIdMap.get(
                (str(snmpEngine.snmpEngineID),
                 variables['transportDomain'],
                 variables['securityModel'],
                 variables['securityLevel'],
                 str(variables['securityName']))
            ),
            mibTreeReq
        )

        k = '#'.join([str(x) for x in (variables['contextEngineId'], variables['contextName'])])
        for x, y in contextIdList:
            if y.match(k):
                mibTreeReq['snmp-context-id'] = macro.expandMacro(x, mibTreeReq)
                break
            else:
                mibTreeReq['snmp-context-id'] = None

        addr = '%s:%s#%s:%s' % (variables['transportAddress'][0], variables['transportAddress'][1], variables['transportAddress'].getLocalAddress()[0], variables['transportAddress'].getLocalAddress()[1])

        for pat, peerId in peerIdMap.get(str(variables['transportDomain']), ()):
            if pat.match(addr):
                mibTreeReq['snmp-peer-id'] = macro.expandMacro(peerId, mibTreeReq)
                break
        else:
            mibTreeReq['snmp-peer-id'] = None

        pdu = variables['pdu']
        k = '#'.join(
            [snmpPduTypesMap.get(variables['pdu'].tagSet, '?'),
             '|'.join([str(x[0]) for x in v2c.apiPDU.getVarBinds(pdu)])]
        )

        for x, y in contentIdList:
            if y.match(k):
                mibTreeReq['snmp-content-id'] = macro.expandMacro(x, mibTreeReq)
                break
            else:
                mibTreeReq['snmp-content-id'] = None

        mibTreeReq['plugins-list'] = pluginIdMap.get(
            (mibTreeReq['snmp-credentials-id'],
             mibTreeReq['snmp-context-id'],
             mibTreeReq['snmp-peer-id'],
             mibTreeReq['snmp-content-id']), []
        )
        mibTreeReq['mib-tree-id'] = routingMap.get(
            (mibTreeReq['snmp-credentials-id'],
             mibTreeReq['snmp-context-id'],
             mibTreeReq['snmp-peer-id'],
             mibTreeReq['snmp-content-id'])
        )

        mibTreeReq['snmp-pdu'] = pdu

        cbCtx.clear()
        cbCtx.update(mibTreeReq)

    #
    # main script starts here
    #

    helpMessage = """\
Usage: %s [--help]
    [--version ]
    [--debug-snmp=<%s>]
    [--debug-asn1=<%s>]
    [--daemonize]
    [--process-user=<uname>] [--process-group=<gname>]
    [--pid-file=<file>]
    [--logging-method=<%s[:args>]>]
    [--log-level=<%s>]
    [--config-file=<file>]""" % (
        sys.argv[0],
        '|'.join([x for x in getattr(pysnmp_debug, 'FLAG_MAP', getattr(pysnmp_debug, 'flagMap', ())) if x != 'mibview']),
        '|'.join([x for x in  getattr(pyasn1_debug, 'FLAG_MAP', getattr(pyasn1_debug, 'flagMap', ()))]),
        '|'.join(log.methodsMap),
        '|'.join(log.levelsMap)
    )

    try:
        opts, params = getopt.getopt(sys.argv[1:], 'hv', [
            'help', 'version', 'debug=', 'debug-snmp=', 'debug-asn1=', 'daemonize',
            'process-user=', 'process-group=', 'pid-file=', 'logging-method=',
            'log-level=', 'config-file='
        ])

    except Exception:
        sys.stderr.write('ERROR: %s\r\n%s\r\n' % (sys.exc_info()[1], helpMessage))
        return

    if params:
        sys.stderr.write('ERROR: extra arguments supplied %s\r\n%s\r\n' % (params, helpMessage))
        return

    pidFile = ''
    cfgFile = CONFIG_FILE
    foregroundFlag = True
    procUser = procGroup = None

    loggingMethod = ['stderr']
    loggingLevel = None

    for opt in opts:
        if opt[0] == '-h' or opt[0] == '--help':
            sys.stderr.write("""\
Synopsis:
  SNMP Command Responder. Runs one or more SNMP command responders (agents)
  and one or more trees of MIB objects representing SNMP-managed entities.
  The tool applies received messages onto one of the MIB trees chosen by
  tool's configuration.

Documentation:
  http://snmplabs.com/snmpresponder/

%s
""" % helpMessage)
            return
        if opt[0] == '-v' or opt[0] == '--version':
            import snmpresponder
            import pysnmp
            import pyasn1
            sys.stderr.write("""\
SNMP Command Responder version %s, written by Ilya Etingof <etingof@gmail.com>
Using foundation libraries: pysnmp %s, pyasn1 %s.
Python interpreter: %s
Software documentation and support at http://snmplabs.com/snmpresponder/
%s
""" % (snmpresponder.__version__, hasattr(pysnmp, '__version__') and pysnmp.__version__ or 'unknown',
               hasattr(pyasn1, '__version__') and pyasn1.__version__ or 'unknown', sys.version, helpMessage))
            return
        elif opt[0] == '--debug-snmp':
            pysnmp_debug.setLogger(pysnmp_debug.Debug(*opt[1].split(','), loggerName=PROGRAM_NAME + '.pysnmp'))
        elif opt[0] == '--debug-asn1':
            pyasn1_debug.setLogger(pyasn1_debug.Debug(*opt[1].split(','), loggerName=PROGRAM_NAME + '.pyasn1'))
        elif opt[0] == '--daemonize':
            foregroundFlag = False
        elif opt[0] == '--process-user':
            procUser = opt[1]
        elif opt[0] == '--process-group':
            procGroup = opt[1]
        elif opt[0] == '--pid-file':
            pidFile = opt[1]
        elif opt[0] == '--logging-method':
            loggingMethod = opt[1].split(':')
        elif opt[0] == '--log-level':
            loggingLevel = opt[1]
        elif opt[0] == '--config-file':
            cfgFile = opt[1]

    with daemon.PrivilegesOf(procUser, procGroup):

        try:
            log.setLogger(PROGRAM_NAME, *loggingMethod, force=True)

            if loggingLevel:
                log.setLevel(loggingLevel)

        except SnmpResponderError:
            sys.stderr.write('%s\r\n%s\r\n' % (sys.exc_info()[1], helpMessage))
            return

    try:
        cfgTree = cparser.Config().load(cfgFile)

    except SnmpResponderError:
        log.error('configuration parsing error: %s' % sys.exc_info()[1])
        return

    if cfgTree.getAttrValue('program-name', '', default=None) != PROGRAM_NAME:
        log.error('config file %s does not match program name %s' % (cfgFile, PROGRAM_NAME))
        return

    if cfgTree.getAttrValue('config-version', '', default=None) != CONFIG_VERSION:
        log.error('config file %s version is not compatible with program version %s' % (cfgFile, CONFIG_VERSION))
        return

    random.seed()

    gCurrentRequestContext = {}

    credIdMap = {}
    peerIdMap = {}
    contextIdList = []
    contentIdList = []
    pluginIdMap = {}
    routingMap = {}
    mibTreeIdMap = {}
    engineIdMap = {}

    transportDispatcher = AsyncoreDispatcher()
    transportDispatcher.registerRoutingCbFun(lambda td, t, d: td)
    transportDispatcher.setSocketMap()  # use global asyncore socket map

    #
    # Initialize plugin modules
    #

    pluginManager = PluginManager(
        macro.expandMacros(
            cfgTree.getAttrValue('plugin-modules-path-list', '', default=[], vector=True),
            {'config-dir': os.path.dirname(cfgFile)}
        ),
        progId=PROGRAM_NAME,
        apiVer=PLUGIN_API_VERSION
    )

    for pluginCfgPath in cfgTree.getPathsToAttr('plugin-id'):
        pluginId = cfgTree.getAttrValue('plugin-id', *pluginCfgPath)
        pluginMod = cfgTree.getAttrValue('plugin-module', *pluginCfgPath)
        pluginOptions = macro.expandMacros(
            cfgTree.getAttrValue('plugin-options', *pluginCfgPath, default=[], vector=True),
            {'config-dir': os.path.dirname(cfgFile)}
        )

        log.info('configuring plugin ID %s (at %s) from module %s with options %s...' % (pluginId, '.'.join(pluginCfgPath), pluginMod, ', '.join(pluginOptions) or '<none>'))

        with daemon.PrivilegesOf(procUser, procGroup):

            try:
                pluginManager.loadPlugin(pluginId, pluginMod, pluginOptions)

            except SnmpResponderError:
                log.error('plugin %s not loaded: %s' % (pluginId, sys.exc_info()[1]))
                return

    for configEntryPath in cfgTree.getPathsToAttr('snmp-credentials-id'):
        credId = cfgTree.getAttrValue('snmp-credentials-id', *configEntryPath)
        configKey = []
        log.info('configuring snmp-credentials %s (at %s)...' % (credId, '.'.join(configEntryPath)))

        engineId = cfgTree.getAttrValue('snmp-engine-id', *configEntryPath)

        if engineId in engineIdMap:
            snmpEngine, snmpContext, snmpEngineMap = engineIdMap[engineId]
            log.info('using engine-id %s' % snmpEngine.snmpEngineID.prettyPrint())
        else:
            snmpEngine = engine.SnmpEngine(snmpEngineID=engineId)
            snmpContext = context.SnmpContext(snmpEngine)
            snmpEngineMap = {
                'transportDomain': {},
                'securityName': {}
            }

            snmpEngine.observer.registerObserver(
                securityAuditObserver,
                'rfc2576.prepareDataElements:sm-failure',
                'rfc3412.prepareDataElements:sm-failure',
                cbCtx=gCurrentRequestContext
            )

            snmpEngine.observer.registerObserver(
                requestObserver,
                'rfc3412.receiveMessage:request',
                cbCtx=gCurrentRequestContext
            )

            snmpEngine.observer.registerObserver(
                usmRequestObserver,
                'rfc3414.processIncomingMsg',
                cbCtx=gCurrentRequestContext
            )

            GetCommandResponder(snmpEngine, snmpContext)
            GetNextCommandResponder(snmpEngine, snmpContext)
            GetBulkCommandResponder(snmpEngine, snmpContext)
            SetCommandResponder(snmpEngine, snmpContext)

            engineIdMap[engineId] = snmpEngine, snmpContext, snmpEngineMap

            log.info('new engine-id %s' % snmpEngine.snmpEngineID.prettyPrint())

        configKey.append(str(snmpEngine.snmpEngineID))

        transportDomain = cfgTree.getAttrValue('snmp-transport-domain', *configEntryPath)
        transportDomain = rfc1902.ObjectName(transportDomain)

        if (transportDomain[:len(udp.domainName)] != udp.domainName and
                udp6 and transportDomain[:len(udp6.domainName)] != udp6.domainName):
            log.error('unknown transport domain %s' % (transportDomain,))
            return

        if transportDomain in snmpEngineMap['transportDomain']:
            bindAddr, transportDomain = snmpEngineMap['transportDomain'][transportDomain]
            log.info('using transport endpoint [%s]:%s, transport ID %s' % (bindAddr[0], bindAddr[1], transportDomain))

        else:
            bindAddr = cfgTree.getAttrValue('snmp-bind-address', *configEntryPath)

            transportOptions = cfgTree.getAttrValue('snmp-transport-options', *configEntryPath, default=[], vector=True)

            try:
                bindAddr, bindAddrMacro = endpoint.parseTransportAddress(transportDomain, bindAddr,
                                                                         transportOptions)

            except SnmpResponderError:
                log.error('bad snmp-bind-address specification %s at %s' % (bindAddr, '.'.join(configEntryPath)))
                return

            if transportDomain[:len(udp.domainName)] == udp.domainName:
                transport = udp.UdpTransport()
            else:
                transport = udp6.Udp6Transport()

            t = transport.openServerMode(bindAddr)

            if 'transparent-proxy' in transportOptions:
                t.enablePktInfo()
                t.enableTransparent()

            elif 'virtual-interface' in transportOptions:
                t.enablePktInfo()

            snmpEngine.registerTransportDispatcher(
                transportDispatcher, transportDomain
            )

            config.addSocketTransport(snmpEngine, transportDomain, t)

            snmpEngineMap['transportDomain'][transportDomain] = bindAddr, transportDomain

            log.info('new transport endpoint [%s]:%s, options %s, transport ID %s' % (bindAddr[0], bindAddr[1], transportOptions and '/'.join(transportOptions) or '<none>', transportDomain))

        configKey.append(transportDomain)

        securityModel = cfgTree.getAttrValue('snmp-security-model', *configEntryPath)
        securityModel = rfc1902.Integer(securityModel)
        securityLevel = cfgTree.getAttrValue('snmp-security-level', *configEntryPath)
        securityLevel = rfc1902.Integer(securityLevel)
        securityName = cfgTree.getAttrValue('snmp-security-name', *configEntryPath)

        if securityModel in (1, 2):
            if securityName in snmpEngineMap['securityName']:
                if snmpEngineMap['securityName'][securityModel] == securityModel:
                    log.info('using security-name %s' % securityName)
                else:
                    raise SnmpResponderError('snmp-security-name %s already in use at snmp-security-model %s' % (securityName, securityModel))
            else:
                communityName = cfgTree.getAttrValue('snmp-community-name', *configEntryPath)
                config.addV1System(snmpEngine, securityName, communityName,
                                   securityName=securityName)
                log.info('new community-name %s, security-model %s, security-name %s, security-level %s' % (communityName, securityModel, securityName, securityLevel))
                snmpEngineMap['securityName'][securityName] = securityModel

            configKey.append(securityModel)
            configKey.append(securityLevel)
            configKey.append(securityName)

        elif securityModel == 3:
            if securityName in snmpEngineMap['securityName']:
                log.info('using USM security-name: %s' % securityName)
            else:
                usmUser = cfgTree.getAttrValue('snmp-usm-user', *configEntryPath)
                securityEngineId = cfgTree.getAttrValue(
                    'snmp-security-engine-id', *configEntryPath, default=None)
                if securityEngineId:
                    securityEngineId = rfc1902.OctetString(securityEngineId)

                log.info('new USM user %s, security-model %s, security-level %s, '
                         'security-name %s, security-engine-id %s' % (usmUser, securityModel, securityLevel,
                                                                      securityName, securityEngineId and securityEngineId.prettyPrint() or '<none>'))

                if securityLevel in (2, 3):
                    usmAuthProto = cfgTree.getAttrValue(
                        'snmp-usm-auth-protocol', *configEntryPath, default=config.usmHMACMD5AuthProtocol)
                    try:
                        usmAuthProto = authProtocols[usmAuthProto.upper()]
                    except KeyError:
                        pass
                    usmAuthProto = rfc1902.ObjectName(usmAuthProto)
                    usmAuthKey = cfgTree.getAttrValue('snmp-usm-auth-key', *configEntryPath)
                    log.info('new USM authentication key: %s, authentication protocol: %s' % (usmAuthKey, usmAuthProto))

                    if securityLevel == 3:
                        usmPrivProto = cfgTree.getAttrValue(
                            'snmp-usm-priv-protocol', *configEntryPath, default=config.usmDESPrivProtocol)
                        try:
                            usmPrivProto = privProtocols[usmPrivProto.upper()]
                        except KeyError:
                            pass
                        usmPrivProto = rfc1902.ObjectName(usmPrivProto)
                        usmPrivKey = cfgTree.getAttrValue('snmp-usm-priv-key', *configEntryPath, default=None)
                        log.info('new USM encryption key: %s, encryption protocol: %s' % (usmPrivKey, usmPrivProto))

                        config.addV3User(
                            snmpEngine, usmUser,
                            usmAuthProto, usmAuthKey,
                            usmPrivProto, usmPrivKey,
                            securityEngineId=securityEngineId
                        )

                    else:
                        config.addV3User(snmpEngine, usmUser,
                                         usmAuthProto, usmAuthKey,
                                         securityEngineId=securityEngineId)

                else:
                    config.addV3User(snmpEngine, usmUser,
                                     securityEngineId=securityEngineId)

                snmpEngineMap['securityName'][securityName] = securityModel

            configKey.append(securityModel)
            configKey.append(securityLevel)
            configKey.append(securityName)

        else:
            raise SnmpResponderError('unknown snmp-security-model: %s' % securityModel)

        configKey = tuple(configKey)
        if configKey in credIdMap:
            log.error('ambiguous configuration for key snmp-credentials-id=%s at %s' % (credId, '.'.join(configEntryPath)))
            return

        credIdMap[configKey] = credId

    duplicates = {}

    for peerCfgPath in cfgTree.getPathsToAttr('snmp-peer-id'):
        peerId = cfgTree.getAttrValue('snmp-peer-id', *peerCfgPath)
        if peerId in duplicates:
            log.error('duplicate snmp-peer-id=%s at %s and %s' % (peerId, '.'.join(peerCfgPath), '.'.join(duplicates[peerId])))
            return

        duplicates[peerId] = peerCfgPath

        log.info('configuring peer ID %s (at %s)...' % (peerId, '.'.join(peerCfgPath)))
        transportDomain = cfgTree.getAttrValue('snmp-transport-domain', *peerCfgPath)
        if transportDomain not in peerIdMap:
            peerIdMap[transportDomain] = []
        for peerAddress in cfgTree.getAttrValue('snmp-peer-address-pattern-list', *peerCfgPath, vector=True):
            for bindAddress in cfgTree.getAttrValue('snmp-bind-address-pattern-list', *peerCfgPath, vector=True):
                peerIdMap[transportDomain].append(
                    (re.compile(peerAddress+'#'+bindAddress), peerId)
                )

    duplicates = {}

    for contextCfgPath in cfgTree.getPathsToAttr('snmp-context-id'):
        contextId = cfgTree.getAttrValue('snmp-context-id', *contextCfgPath)
        if contextId in duplicates:
            log.error('duplicate snmp-context-id=%s at %s and %s' % (contextId, '.'.join(contextCfgPath), '.'.join(duplicates[contextId])))
            return

        duplicates[contextId] = contextCfgPath

        k = '#'.join(
            (cfgTree.getAttrValue('snmp-context-engine-id-pattern', *contextCfgPath),
             cfgTree.getAttrValue('snmp-context-name-pattern', *contextCfgPath))
        )

        log.info('configuring context ID %s (at %s), composite key: %s' % (contextId, '.'.join(contextCfgPath), k))

        contextIdList.append((contextId, re.compile(k)))

    duplicates = {}

    for contentCfgPath in cfgTree.getPathsToAttr('snmp-content-id'):
        contentId = cfgTree.getAttrValue('snmp-content-id', *contentCfgPath)
        if contentId in duplicates:
            log.error('duplicate snmp-content-id=%s at %s and %s' % (contentId, '.'.join(contentCfgPath), '.'.join(duplicates[contentId])))
            return

        duplicates[contentId] = contentCfgPath

        for x in cfgTree.getAttrValue('snmp-pdu-oid-prefix-pattern-list', *contentCfgPath, vector=True):
            k = '#'.join([cfgTree.getAttrValue('snmp-pdu-type-pattern', *contentCfgPath), x])

            log.info('configuring content ID %s (at %s), composite key: %s' % (contentId, '.'.join(contentCfgPath), k))

            contentIdList.append((contentId, re.compile(k)))

    del duplicates

    for pluginCfgPath in cfgTree.getPathsToAttr('using-plugin-id-list'):
        pluginIdList = cfgTree.getAttrValue('using-plugin-id-list', *pluginCfgPath, vector=True)
        log.info('configuring plugin ID(s) %s (at %s)...' % (','.join(pluginIdList), '.'.join(pluginCfgPath)))
        for credId in cfgTree.getAttrValue('matching-snmp-credentials-id-list', *pluginCfgPath, vector=True):
            for peerId in cfgTree.getAttrValue('matching-snmp-peer-id-list', *pluginCfgPath, vector=True):
                for contextId in cfgTree.getAttrValue('matching-snmp-context-id-list', *pluginCfgPath, vector=True):
                    for contentId in cfgTree.getAttrValue('matching-snmp-content-id-list', *pluginCfgPath, vector=True):
                        k = credId, contextId, peerId, contentId
                        if k in pluginIdMap:
                            log.error('duplicate snmp-credentials-id %s, snmp-context-id %s, snmp-peer-id %s, snmp-content-id %s at plugin-id(s) %s' % (credId, contextId, peerId, contentId, ','.join(pluginIdList)))
                            return
                        else:
                            log.info('configuring plugin(s) %s (at %s), composite key: %s' % (','.join(pluginIdList), '.'.join(pluginCfgPath), '/'.join(k)))

                            for pluginId in pluginIdList:
                                if not pluginManager.hasPlugin(pluginId):
                                    log.error('undefined plugin ID %s referenced at %s' % (pluginId, '.'.join(pluginCfgPath)))
                                    return

                            pluginIdMap[k] = pluginIdList

    for routeCfgPath in cfgTree.getPathsToAttr('using-mib-tree-id'):
        mibTreeId = cfgTree.getAttrValue('using-mib-tree-id', *routeCfgPath)
        log.info('configuring destination MIB tree ID(s) %s (at %s)...' % (mibTreeId, '.'.join(routeCfgPath)))
        for credId in cfgTree.getAttrValue('matching-snmp-credentials-id-list', *routeCfgPath, vector=True):
            for peerId in cfgTree.getAttrValue('matching-snmp-peer-id-list', *routeCfgPath, vector=True):
                for contextId in cfgTree.getAttrValue('matching-snmp-context-id-list', *routeCfgPath, vector=True):
                    for contentId in cfgTree.getAttrValue('matching-snmp-content-id-list', *routeCfgPath, vector=True):
                        k = credId, contextId, peerId, contentId
                        if k in routingMap:
                            log.error('duplicate snmp-credentials-id %s, snmp-context-id %s, snmp-peer-id %s, snmp-content-id %s at mib-tree-id(s) %s' % (credId, contextId, peerId, contentId, ','.join(mibTreeIdList)))
                            return
                        else:
                            routingMap[k] = mibTreeId

                        log.info('configuring MIB tree routing to %s (at %s), composite key: %s' % (mibTreeId, '.'.join(routeCfgPath), '/'.join(k)))

    for mibTreeCfgPath in cfgTree.getPathsToAttr('mib-tree-id'):
        mibTreeId = cfgTree.getAttrValue('mib-tree-id', *mibTreeCfgPath)

        log.info('configuring MIB tree ID %s (at %s)...' % (
            mibTreeId, '.'.join(mibTreeCfgPath)))

        mibTextPaths = cfgTree.getAttrValue(
            'mib-text-search-path-list', *mibTreeCfgPath,
            default=[], vector=True)

        mibCodePatternPaths = cfgTree.getAttrValue(
            'mib-code-modules-pattern-list', *mibTreeCfgPath,
            default=[], vector=True)

        mibBuilder = builder.MibBuilder()

        compiler.addMibCompiler(mibBuilder, sources=mibTextPaths)

        for topDir in mibCodePatternPaths:

            filenameRegExp = re.compile(os.path.basename(topDir))
            topDir = os.path.dirname(topDir)

            for root, dirs, files in os.walk(topDir):

                if not files or root.endswith('__pycache__'):
                    continue

                mibBuilder.setMibSources(
                    builder.DirMibSource(root), *mibBuilder.getMibSources()
                )

                for filename in files:

                    if not filenameRegExp.match(filename):
                        log.debug('skipping non-matching file %s while loading '
                                  'MIB tree ID %s' % (filename, mibTreeId))
                        continue

                    module, _ = os.path.splitext(filename)

                    try:
                        mibBuilder.loadModule(module)

                    except PySnmpError as ex:
                        log.error('fail to load MIB implementation from file '
                                  '%s into MIB tree ID %s' % (
                            os.path.join(root, filename), mibTreeId))
                        raise SnmpResponderError(str(ex))

                    log.info('loaded MIB implementation file '
                             '%s into MIB tree ID %s' % (
                        os.path.join(root, filename), mibTreeId))

        mibTreeIdMap[mibTreeId] = instrum.MibInstrumController(mibBuilder)

        log.info('loaded new MIB tree ID %s' % mibTreeId)

    if not foregroundFlag:
        try:
            daemon.daemonize(pidFile)

        except Exception:
            log.error('can not daemonize process: %s' % sys.exc_info()[1])
            return

    # Run mainloop

    log.info('starting I/O engine...')

    transportDispatcher.jobStarted(1)  # server job would never finish

    with daemon.PrivilegesOf(procUser, procGroup, final=True):

        while True:
            try:
                transportDispatcher.runDispatcher()

            except (PySnmpError, SnmpResponderError, socket.error):
                log.error(str(sys.exc_info()[1]))
                continue

            except Exception:
                transportDispatcher.closeDispatcher()
                raise


if __name__ == '__main__':
    rc = 1

    try:
        main()

    except KeyboardInterrupt:
        log.info('shutting down process...')
        rc = 0

    except Exception:
        for line in traceback.format_exception(*sys.exc_info()):
            log.error(line.replace('\n', ';'))

    log.info('process terminated')

    sys.exit(rc)
