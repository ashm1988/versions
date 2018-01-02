data = {
    "server": ['Server: ', ".//Item[@name='System']/Item[@name='Hostname']"],
    "instance": ['Instance name: ', ".//Item[@name='Identity']/Item[@name='Name']"],
    "product": ['Product: ', ".//Item[@name='Identity']/Item[@name='Description']"],
    "core": ['Core Version: ', ".//Item[@name='Identity']/Item[@name='Version']"],
    "otl": ['OTL Version: ', ".//Item[@name='Exchange Adapters']//Item[@name='Version']"],
    "licence": ['Licence Expiry: ', ".//Item[@name='Licence']/Item[@name='Expiry']"],
    "adapter": ['Adapter Logging Enabled: ', ".//Item[@name='Exchange Adapters']//Item[@name='Configuration']//Item[@name='Enabled']"],
    "frapi": ['FRAPI Logging Enabled: ', ".//Item[@name='Client Adapters']//Item[@name='FRAPI2']//Item[@name='Enabled']"]

}



print data.locals()