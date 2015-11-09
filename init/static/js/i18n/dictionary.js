var fr_t_dictionary = {
 'Yes': 'Oui',
 'No': 'Non',
 'Are you sure ?': 'Etes-vous certain ?',
 'done': 'fait',
 'running': 'en cours',
 'waiting': 'en attente',
 'queued': 'en queue',
 'cancelled': 'annulé',
 'Tools': 'Outils',
 'No menu entry found matching filter': 'Aucune entrée du menu ne correspond au filtre',
 'Loading data': 'Chargement des données',
 'Nodes performance': 'Performance des noeuds',
 'Nodes SAN topology': 'Topologie SAN des noeuds',
 'Nodes differences': 'Différences entre noeuds',
 'Services differences': 'Différences entre services',
 'Services topology': 'Topologie des services',
 'Actions on selected resources': 'Actions sur les resources sélectionnées',
 'Actions on selected service instances': 'Actions sur les services sélectionnés',
 'Actions on selected nodes': 'Actions sur les noeuds sélectionnés',
 'Actions on selected modules': 'Actions sur les modules sélectionnés',
 'Actions on node': 'Actions sur le noeud',
 'Actions on <b>{{svcname}}</b> service instance on node <b>{{nodename}}</b>': "Actions sur l'instance du service <b>{{svcname}}</b> sur le noeud <b>{{nodename}}</b>",
 'Actions on resource <b>{{rid}}</b> of <b>{{svcname}}</b> service instance on node <b>{{nodename}}</b>': "Actions sur la ressource <b>{{rid}}</b> de l'instance du service <b>{{svcname}}</b> sur le noeud <b>{{nodename}}</b>",
 'Actions on module <b>{{module}}</b> on <b>{{svcname}}</b> service instance on node <b>{{nodename}}</b>': "Actions sur le module <b>{{module}}</b> sur l'instance du service  <b>{{svcname}}</b> sur le noeud <b>{{nodename}}</b>",
 'Actions on module <b>{{module}}</b> on node <b>{{nodename}}</b>': "Actions sur le module <b>{{module}}</b> sur le noeud <b>{{nodename}}</b>"
}

var t_dictionary = {
 'fr-FR': fr_t_dictionary,
 'fr': fr_t_dictionary
}

// Init i18n
function i18n_init(callback) {
  i18n.init({
      debug: true,
      fallbackLng: false,
      load:'unspecific',
      resGetPath: "/init/static/locales/__lng__/__ns__.json",
      ns: {
          namespaces: ['translation'],
          defaultNs: 'translation'
      }
  }, callback);
}